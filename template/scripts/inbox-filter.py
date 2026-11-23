#!/usr/bin/env python3
"""Inbox fetcher with a deterministic sender filter. No LLM runs here.

One Gmail mailbox, read via the `gog` CLI with read-only Gmail + Calendar scopes.
Mail is kept only if
  1. the From address is on the allowlist, AND
  2. Gmail's Authentication-Results says dmarc=pass (or, if the sender's domain
     publishes no DMARC, dkim=pass for that domain), so a forged From is dropped.
Everything else is dropped in code: no subject, body or snippet is read for
dropped mail, and none of it is written anywhere. Only the message id and the
drop reason are recorded, so it is never re-examined.

The Ops session runs `fetch`, then hands only the files this script writes to
memory/inbox-filter/inbox/ to the Read-only triage subagent.

Allowlist (data, not code):
  - comms.trusted_senders in config/workspace.json (email entries) are always
    allowed. Edit that list by re-running init or by hand; never from a model.
  - memory/inbox-filter/allowlist.json holds the mutable part:
        {"approved": [], "blocked": [], "dkim_aliases": {}}
    `allow` / `block` edit it, only on the principal's explicit word.
  - dkim_aliases pins extra DKIM signing domains for a sender domain that has
    no SPF/DMARC/own DKIM (for example a small Google Workspace domain signed
    only by d=<tenant>.<date>.gappssmtp.com):
        {"example.com": ["example-com.20230601.gappssmtp.com"]}

Unknown senders: a sender on neither list whose mail passes DMARC/DKIM is
queued in state["pendingAsk"] (address and count only, never subject or body).
Ops asks the principal whether to allow it, then runs `ask-done`. Forged mail
is dropped without asking. Only the address, after a strict format check, ever
reaches a model.

Config (config/workspace.json):
  inbox.account       the mailbox address (required)
  inbox.gog_path      path to gog (default: found on PATH, then /opt/homebrew/bin/gog)
  inbox.window_days   fetch window (default 14)

Usage:
  inbox-filter.py senders [--days N]   distinct From addresses + counts (no subjects/bodies)
  inbox-filter.py fetch                new allowed mail -> inbox/, prints a JSON summary
  inbox-filter.py calendar [--days N]  upcoming events on the mailbox's calendar (JSON)
  inbox-filter.py ask-done ADDR...     Ops: the principal has been asked about these
  inbox-filter.py allow ADDR           Admin, on the principal's word: approve + re-fetch its dropped mail
  inbox-filter.py block ADDR           Admin, on the principal's word: never ask again
  inbox-filter.py enrich PATH...       re-run link analysis on kept files
"""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import timedelta
from email.utils import parseaddr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import link_check  # noqa: E402  deterministic phish check + fetch
import workspace_config as wc  # noqa: E402

BASE = wc.MEMORY / "inbox-filter"
ALLOW_FILE = BASE / "allowlist.json"
STATE_FILE = BASE / "state.json"
INBOX = BASE / "inbox"
MAX_BODY = 20000
WINDOW_DAYS = int(wc.get("inbox.window_days", 14))
QUERY = f"newer_than:{WINDOW_DAYS}d -in:spam -in:trash -in:sent -in:drafts"
ADDR_RE = re.compile(r"^[a-z0-9._%+-]{1,64}@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,24}$")


def die(msg):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def account():
    a = (wc.get("inbox.account") or "").strip().lower()
    if not ADDR_RE.match(a):
        die("inbox.account is not set in config/workspace.json")
    return a


def gog_bin():
    p = wc.get("inbox.gog_path") or shutil.which("gog") or "/opt/homebrew/bin/gog"
    if not os.path.exists(p):
        die(f"gog CLI not found ({p}); install it or set inbox.gog_path")
    return p


def gog(*args):
    r = subprocess.run([gog_bin(), *args, "--account", account(), "--json", "--no-input"],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"gog {' '.join(args[:3])} failed: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout or "{}")


def addr(from_header):
    return parseaddr(from_header or "")[1].strip().lower()


def load_allow_file():
    try:
        d = json.loads(ALLOW_FILE.read_text())
    except FileNotFoundError:
        d = {}
    d.setdefault("approved", [])
    d.setdefault("blocked", [])
    d.setdefault("dkim_aliases", {})
    return d


def save_allow_file(d):
    BASE.mkdir(parents=True, exist_ok=True)
    tmp = ALLOW_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1) + "\n")
    tmp.replace(ALLOW_FILE)


def load_allow():
    d = load_allow_file()
    return {a.strip().lower() for a in wc.trusted_emails() + d["approved"] if a.strip()}


def load_state():
    st = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"seen": {}, "lastRun": None}
    st.setdefault("seen", {})
    st.setdefault("pendingAsk", {})
    st.setdefault("asked", {})
    return st


def save_state(st):
    BASE.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1) + "\n")
    tmp.replace(STATE_FILE)


def list_messages(query, cap=500):
    out, page = [], None
    while len(out) < cap:
        args = ["gmail", "messages", "search", query, "--max", "100"]
        if page:
            args += ["--page", page]
        d = gog(*args)
        out += d.get("messages") or []
        page = d.get("nextPageToken")
        if not page:
            break
    return out


def authenticated(msg_id, sender):
    """True only if Gmail recorded DMARC pass (or DKIM pass for the sender's domain)."""
    m = gog("gmail", "get", msg_id, "--format", "metadata", "--headers", "Authentication-Results")
    hdrs = (m.get("message", {}).get("payload", {}) or {}).get("headers", []) or []
    ar = " ".join(h.get("value", "") for h in hdrs if h.get("name", "").lower() == "authentication-results").lower()
    if not ar:
        return False, "no-auth-results"
    if "dmarc=pass" in ar:
        return True, "dmarc-pass"
    if "dmarc=" in ar and "dmarc=none" not in ar:
        return False, "dmarc-fail"
    dom = sender.split("@")[-1]
    if re.search(r"dkim=pass[^;]*header\.(i|d)=@?[\w.-]*" + re.escape(dom) + r"\b", ar):
        return True, "dkim-pass"
    for alias in load_allow_file()["dkim_aliases"].get(dom, []):
        if re.search(r"dkim=pass[^;]*header\.(i|d)=@?" + re.escape(alias.lower()) + r"\b", ar):
            return True, "dkim-pinned-alias"
    return False, "unauthenticated"


def _walk_text(payload):
    plain, html = [], []

    def walk(p):
        mt = p.get("mimeType", "")
        data = (p.get("body") or {}).get("data")
        if data and mt in ("text/plain", "text/html"):
            txt = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")
            (plain if mt == "text/plain" else html).append(txt)
        for c in p.get("parts") or []:
            walk(c)

    walk(payload or {})
    return plain, html


def body_text(payload):
    """Plain-text body from a full-format payload (prefers text/plain)."""
    plain, html = _walk_text(payload)
    if plain:
        return "\n".join(plain)
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", "\n".join(html), flags=re.S | re.I)
    txt = re.sub(r"<br\s*/?>|</p>|</div>", "\n", txt, flags=re.I)
    return re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", "", txt))


def link_report(payload):
    plain, html = _walk_text(payload)
    return link_check.analyze(link_check.extract_links(plain, html))


def attachments(payload):
    names = []

    def walk(p):
        if p.get("filename"):
            names.append(p["filename"])
        for c in p.get("parts") or []:
            walk(c)

    walk(payload or {})
    return names


def cmd_senders(days):
    counts = {}
    for m in list_messages(f"newer_than:{days}d -in:spam -in:trash -in:sent -in:drafts", cap=2000):
        a = addr(m.get("from"))
        counts[a] = counts.get(a, 0) + 1
    allow = load_allow()
    for a, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"{n:5d}  {a}{'  (allowed)' if a in allow else ''}")


def cmd_fetch():
    allow, st = load_allow(), load_state()
    blocked = {b.lower() for b in load_allow_file()["blocked"]}
    INBOX.mkdir(parents=True, exist_ok=True)
    kept, dropped, errors = [], {}, []
    for m in list_messages(QUERY):
        mid = m.get("id")
        if not mid or mid in st["seen"]:
            continue
        sender = addr(m.get("from"))
        if sender in blocked:
            st["seen"][mid] = "drop:blocked"
            dropped["blocked"] = dropped.get("blocked", 0) + 1
            continue
        if sender not in allow:
            # Record the address so `allow` can re-fetch this mail later.
            st["seen"][mid] = "drop:unknown:" + (sender if ADDR_RE.match(sender) else "invalid")
            dropped["sender-not-allowlisted"] = dropped.get("sender-not-allowlisted", 0) + 1
            if ADDR_RE.match(sender) and sender not in st["asked"]:
                if sender in st["pendingAsk"]:
                    st["pendingAsk"][sender]["count"] += 1
                else:
                    try:
                        ok, _ = authenticated(mid, sender)
                    except Exception:
                        ok = False
                        st["seen"].pop(mid, None)  # retry next run
                    if ok:
                        st["pendingAsk"][sender] = {"count": 1, "first": wc.now_iso()}
            continue
        try:
            ok, why = authenticated(mid, sender)
            if not ok:
                st["seen"][mid] = f"drop:{why}"
                dropped[why] = dropped.get(why, 0) + 1
                continue
            full = gog("gmail", "get", mid, "--format", "full")
            msg = full.get("message", {})
            h = full.get("headers", {})
            rec = {
                "id": mid, "threadId": msg.get("threadId"), "date": h.get("date"),
                "from": sender, "to": h.get("to"), "cc": h.get("cc"), "subject": h.get("subject"),
                "auth": why, "attachments": attachments(msg.get("payload")),
                "body": body_text(msg.get("payload"))[:MAX_BODY],
                "links": link_report(msg.get("payload")),
                "fetchedAt": wc.now_iso(),
                "status": "new",
            }
            path = INBOX / f"{wc.now().strftime('%Y%m%d')}-{mid}.json"
            path.write_text(json.dumps(rec, indent=1) + "\n")
            st["seen"][mid] = "kept"
            kept.append(str(path))
        except Exception as e:  # leave unseen so the next run retries
            errors.append(f"{mid}: {e}"[:300])
    st["lastRun"] = wc.now_iso()
    save_state(st)
    # Every kept file still marked "new" (this run's, plus any earlier run whose
    # triage never finished), so nothing is lost if Ops dies mid-triage.
    pending = sorted(str(f) for f in INBOX.glob("*.json")
                     if json.loads(f.read_text()).get("status") == "new")
    print(json.dumps({"kept": kept, "pending": pending, "dropped": dropped, "errors": errors,
                      "unknownSenders": st["pendingAsk"], "lastRun": st["lastRun"]}, indent=1))
    return 1 if errors else 0


def cmd_calendar(days):
    now = wc.now()
    d = gog("calendar", "events", account(), "--from", now.isoformat(timespec="seconds"),
            "--to", (now + timedelta(days=days)).isoformat(timespec="seconds"), "--max", "250")
    print(json.dumps(d, indent=1))


def cmd_enrich(paths):
    """Add the link analysis to already-kept files and mark them new for re-triage."""
    inbox = INBOX.resolve()
    for p in paths:
        f = os.path.realpath(p)
        if os.path.dirname(f) != str(inbox):
            die(f"{p} is not in {INBOX}")
        rec = json.loads(open(f).read())
        full = gog("gmail", "get", rec["id"], "--format", "full")
        rec["links"] = link_report(full.get("message", {}).get("payload"))
        rec["status"] = "new"
        with open(f, "w") as fh:
            fh.write(json.dumps(rec, indent=1) + "\n")
        print(p, [(lk["verdict"], lk["url"][:70]) for lk in rec["links"]])


def cmd_ask_done(addrs):
    st = load_state()
    for a in (x.strip().lower() for x in addrs):
        if a in st["pendingAsk"]:
            st["pendingAsk"].pop(a)
            st["asked"][a] = wc.now_iso()
            print("asked", a)
    save_state(st)


def cmd_allow(a):
    a = a.strip().lower()
    if not ADDR_RE.match(a):
        die(f"not an email address: {a!r}")
    d = load_allow_file()
    if a not in d["approved"]:
        d["approved"].append(a)
    d["blocked"] = [b for b in d["blocked"] if b != a]
    save_allow_file(d)
    st = load_state()
    st["pendingAsk"].pop(a, None)
    st["asked"].pop(a, None)
    cleared = [k for k, v in st["seen"].items() if v == "drop:unknown:" + a]
    for k in cleared:
        st["seen"].pop(k)
    save_state(st)
    print(f"allowed {a}; {len(cleared)} earlier email(s) will be fetched on the next run")


def cmd_block(a):
    a = a.strip().lower()
    if not ADDR_RE.match(a):
        die(f"not an email address: {a!r}")
    d = load_allow_file()
    if a not in d["blocked"]:
        d["blocked"].append(a)
    d["approved"] = [x for x in d["approved"] if x != a]
    save_allow_file(d)
    st = load_state()
    st["pendingAsk"].pop(a, None)
    st["asked"][a] = st["asked"].get(a) or wc.now_iso()
    save_state(st)
    print(f"blocked {a}")


def main():
    ap = argparse.ArgumentParser(description="Deterministic inbox filter (see module docstring).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("senders")
    s.add_argument("--days", type=int, default=180)
    sub.add_parser("fetch")
    c = sub.add_parser("calendar")
    c.add_argument("--days", type=int, default=14)
    k = sub.add_parser("ask-done")
    k.add_argument("addrs", nargs="+")
    e = sub.add_parser("enrich")
    e.add_argument("paths", nargs="+")
    w = sub.add_parser("allow")
    w.add_argument("addr")
    b = sub.add_parser("block")
    b.add_argument("addr")
    a = ap.parse_args()
    if a.cmd == "enrich":
        return cmd_enrich(a.paths)
    if a.cmd == "ask-done":
        return cmd_ask_done(a.addrs)
    if a.cmd == "allow":
        return cmd_allow(a.addr)
    if a.cmd == "block":
        return cmd_block(a.addr)
    if a.cmd == "senders":
        return cmd_senders(a.days)
    if a.cmd == "fetch":
        return cmd_fetch()
    return cmd_calendar(a.days)


if __name__ == "__main__":
    sys.exit(main() or 0)
