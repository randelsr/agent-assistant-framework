#!/usr/bin/env python3
"""Send one narrowly scoped email. This is the ONLY email the agent may send.

Typical use: a weekly agenda or digest, from one fixed mailbox to a fixed list
of recipients. Off by default: with send_email.from or send_email.to empty in
config/workspace.json, every command refuses.

Guards, all deterministic:
  - Sender and recipients come from config/workspace.json only. Nothing on the
    command line can change them. (Protect that file: settings.json denies the
    model Edit/Write on it, and changes should come from re-running init.)
  - The OAuth token has ONE scope, gmail.send. It's checked on every send, and
    the script refuses if any other scope is present or if the token belongs to
    another account. It's kept in the macOS Keychain, apart from any read-only
    token, so a read-only CLI still cannot send.
  - The body must be a file in memory/send-outbox/ named YYYY-MM-DD.md.
  - One send per date. sent.json records each one; a second send for the same
    date is refused.
  - Quiet hours (comms.quiet_hours_start/end, principal.timezone) apply.
  - Plain text, no attachments, no reply, no threading.

Config (config/workspace.json):
  send_email.from              the sending mailbox (required)
  send_email.from_display      display name (default: agent name)
  send_email.to                list of recipients (required, non-empty)
  send_email.subject           subject template; {date} and {agent} are filled
                               (default "{agent} update: {date}")
  send_email.credentials_path  OAuth client JSON with client_id/client_secret
                               (default: gog's credentials.json)
  send_email.keychain_service  default "<short>/gmail-send"

Usage:
  scoped-send-email.py auth                 one time: the mailbox owner approves gmail.send
  scoped-send-email.py check                verify the token and its scope
  scoped-send-email.py send PATH [--dry-run]
"""

import base64
import http.server
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

SCOPE = "https://www.googleapis.com/auth/gmail.send"
# Gmail API messages.send for the authorized mailbox ("me").
SEND_ENDPOINT = urllib.parse.urljoin("https://gmail.googleapis.com/gmail/v1/", "users/me/messages/send")
OUTBOX = wc.MEMORY / "send-outbox"
SENT = OUTBOX / "sent.json"
NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
ADDR_RE = re.compile(r"^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24}$")
DEFAULT_CREDS = Path.home() / "Library/Application Support/gogcli/credentials.json"


def die(msg):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def settings():
    frm = (wc.get("send_email.from") or "").strip().lower()
    to = tuple(t.strip() for t in (wc.get("send_email.to") or []) if isinstance(t, str) and t.strip())
    if not frm or not to:
        die("scoped send is not configured (send_email.from / send_email.to empty in config/workspace.json)")
    for a in (frm, *to):
        if not ADDR_RE.match(a):
            die(f"invalid address in config: {a!r}")
    return frm, to


def kc_service():
    return wc.get("send_email.keychain_service") or wc.keychain_service("gmail-send")


def client():
    path = Path(os.path.expanduser(wc.get("send_email.credentials_path") or str(DEFAULT_CREDS)))
    try:
        c = json.loads(path.read_text())
    except Exception:
        die(f"cannot read OAuth client credentials at {path}")
    c = c.get("installed") or c.get("web") or c
    return c["client_id"], c["client_secret"]


def kc_get():
    r = subprocess.run(["security", "find-generic-password", "-s", kc_service(), "-a", wc.keychain_account(), "-w"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def kc_set(token):
    subprocess.run(["security", "add-generic-password", "-U", "-s", kc_service(), "-a", wc.keychain_account(),
                    "-w", token], check=True, capture_output=True)


def post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def access_token(frm):
    rt = kc_get()
    if not rt:
        die("no send token. Run: scoped-send-email.py auth")
    cid, cs = client()
    tok = post_form("https://oauth2.googleapis.com/token",
                    {"client_id": cid, "client_secret": cs, "refresh_token": rt, "grant_type": "refresh_token"})
    at = tok["access_token"]
    with urllib.request.urlopen("https://oauth2.googleapis.com/tokeninfo?access_token=" + urllib.parse.quote(at),
                                timeout=30) as r:
        info = json.loads(r.read())
    scopes = set(info.get("scope", "").split())
    if scopes != {SCOPE}:
        die(f"token scopes are {sorted(scopes)}; expected exactly gmail.send")
    if info.get("email") and info["email"].lower() != frm:
        die(f"token belongs to {info['email']}, not {frm}")
    return at


def cmd_auth():
    frm, _ = settings()
    cid, cs = client()
    state = secrets.token_urlsafe(16)
    got = {}
    label = wc.agent_name().encode()

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                got["code"] = q["code"][0]
                body = label + b": send permission received. You can close this tab."
            else:
                body = label + b": no code received."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}/"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "login_hint": frm, "state": state})
    print(f"Sign in as {frm} and approve 'Send email on your behalf':\n{url}", flush=True)
    webbrowser.open(url)
    srv.timeout = 60
    for _ in range(15):  # up to 15 minutes
        srv.handle_request()
        if "code" in got:
            break
    if "code" not in got:
        die("timed out waiting for approval")
    tok = post_form("https://oauth2.googleapis.com/token",
                    {"client_id": cid, "client_secret": cs, "code": got["code"], "redirect_uri": redirect,
                     "grant_type": "authorization_code"})
    if set(tok.get("scope", "").split()) != {SCOPE}:
        die(f"granted scopes {tok.get('scope')}; expected exactly gmail.send. Token NOT saved.")
    if "refresh_token" not in tok:
        die("no refresh token returned. Token NOT saved.")
    kc_set(tok["refresh_token"])
    access_token(frm)  # verify
    print("OK: send-only token saved to Keychain service", kc_service())


def load_sent():
    try:
        return json.loads(SENT.read_text())
    except Exception:
        return {}


def cmd_send(path, dry):
    frm, to = settings()
    p = Path(path).resolve()
    if p.parent != OUTBOX.resolve():
        die(f"body must be in {OUTBOX}")
    m = NAME_RE.match(p.name)
    if not m or not p.is_file():
        die("body file must exist and be named YYYY-MM-DD.md")
    date = m.group(1)
    body = p.read_text().strip()
    if not body or len(body) > 20000:
        die("body empty or too long")
    sent = load_sent()
    if date in sent:
        die(f"message for {date} already sent at {sent[date]['at']}")
    now = wc.now()
    if wc.in_quiet_hours(now):
        qs, qe = wc.quiet_hours()
        die(f"inside quiet hours {qs:02d}:00-{qe:02d}:00 (now {now:%H:%M} {now.tzname()})")
    d = datetime.strptime(date, "%Y-%m-%d")
    subject_tpl = wc.get("send_email.subject") or "{agent} update: {date}"
    msg = EmailMessage()
    msg["From"] = f"{wc.get('send_email.from_display') or wc.agent_name()} <{frm}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject_tpl.format(agent=wc.agent_name(), date=f"{d:%a %b} {d.day}")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=frm.split("@")[-1])
    msg.set_content(body + "\n")
    if dry:
        print(msg.as_string())
        print("DRY RUN: nothing sent")
        return
    at = access_token(frm)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    req = urllib.request.Request(SEND_ENDPOINT,
                                 data=json.dumps({"raw": raw}).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read())
    sent[date] = {"at": now.isoformat(timespec="seconds"), "id": res.get("id"), "to": list(to)}
    OUTBOX.mkdir(parents=True, exist_ok=True)
    SENT.write_text(json.dumps(sent, indent=2) + "\n")
    print(f"SENT {date} id={res.get('id')} to {', '.join(to)}")


def main():
    a = sys.argv[1:]
    if a[:1] == ["auth"]:
        cmd_auth()
    elif a[:1] == ["check"]:
        frm, _ = settings()
        access_token(frm)
        print("OK: token valid, scope gmail.send only, account", frm)
    elif a[:1] == ["send"] and len(a) >= 2:
        cmd_send(a[1], "--dry-run" in a[2:])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
