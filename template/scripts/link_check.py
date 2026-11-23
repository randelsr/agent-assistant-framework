#!/usr/bin/env python3
"""Deterministic phishing check + fetch for links in allowlisted mail.

Policy: when a trusted sender's mail contains a link, run a phishing analysis on
it and follow it only if it passes.

No model is involved in the verdict. A link is followed only if every check
passes, at every redirect hop. The fetch is anonymous (no cookies, no
credentials, no JavaScript), so the risk is limited to what the text says; that
text is then treated as untrusted email content by the Read-only triage agent.

Verdicts: "pass" (followed), "fail" (phishing signal, never followed, reasons
recorded), "skip" (safe-looking but not worth following: unsubscribe, social,
mailto, images).

Local additions (config/workspace.json, optional):
  "link_check": {
    "extra_brands": {"yourcompany": ["yourcompany.com", "yourcompany.net"]},
    "extra_risky_suffixes": ["example-freehost.com"]
  }
Add the brands your principal is most likely to be phished with: their employer,
their bank, their school district, their payroll provider. A host that looks
like one of these but is not on its official list fails.

CLI (for spot checks):  link_check.py URL [ANCHOR_TEXT]
"""

import html as htmlmod
import ipaddress
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

MAX_LINKS = 8          # per email
MAX_BYTES = 400_000    # per fetched page
MAX_CHARS = 15_000     # text kept per page
MAX_HOPS = 5
UA = "Mozilla/5.0 (inbox-filter link reader)"

# Hosting that phishers use because anyone can publish there in seconds.
RISKY_SUFFIXES = (
    "ngrok.io", "ngrok-free.app", "duckdns.org", "no-ip.org", "web.app", "firebaseapp.com",
    "glitch.me", "r2.dev", "pages.dev", "workers.dev", "repl.co", "replit.app", "vercel.app",
    "netlify.app", "weebly.com", "wixsite.com", "square.site", "000webhostapp.com",
    "blogspot.com", "ipfs.io", "trycloudflare.com", "github.io", "onrender.com", "azurewebsites.net",
    "storage.googleapis.com", "blob.core.windows.net", "s3.amazonaws.com", "zohosites.com",
) + tuple(wc.get("link_check.extra_risky_suffixes", []) or [])
RISKY_TLDS = {"zip", "mov", "top", "xyz", "click", "country", "kim", "work", "gq", "tk", "ml", "cf", "ga", "rest", "cam", "icu"}

# Brands people get phished with, and their official domains. A host that LOOKS
# like one but isn't on its list fails.
OFFICIAL = {
    "google": ["google.com", "googleusercontent.com", "goo.gl", "youtube.com", "gstatic.com"],
    "microsoft": ["microsoft.com", "live.com", "office.com", "sharepoint.com", "outlook.com"],
    "office": ["office.com", "office365.com"], "outlook": ["outlook.com", "office.com"],
    "apple": ["apple.com"], "icloud": ["icloud.com"], "paypal": ["paypal.com"], "venmo": ["venmo.com"],
    "amazon": ["amazon.com", "amazonaws.com"], "wellsfargo": ["wellsfargo.com"], "chase": ["chase.com"],
    "bankofamerica": ["bankofamerica.com"], "docusign": ["docusign.com", "docusign.net"],
    "dropbox": ["dropbox.com"], "facebook": ["facebook.com", "fb.com"], "instagram": ["instagram.com"],
    "netflix": ["netflix.com"], "zelle": ["zellepay.com"], "linkedin": ["linkedin.com", "lnkd.in"],
    "slack": ["slack.com"], "zoom": ["zoom.us", "zoom.com"], "okta": ["okta.com"],
    "adobe": ["adobe.com"], "github": ["github.com", "githubusercontent.com"],
}
for _b, _doms in (wc.get("link_check.extra_brands", {}) or {}).items():
    OFFICIAL[str(_b).lower()] = [str(d).lower() for d in _doms]
BRANDS = list(OFFICIAL)
# Short or common words that appear inside unrelated hostnames.
NO_SUBSTRING_MATCH = {"office", "chase", "zoom", "okta", "slack", "apple"}

SKIP_HOSTS = ("facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com", "youtube.com",
              "tiktok.com", "pinterest.com", "apps.apple.com", "play.google.com")
SKIP_WORDS = ("unsubscribe", "optout", "opt-out", "preferences", "privacy", "manage-subscription", "viewinbrowser")
DOWNLOAD_EXT = re.compile(r"\.(exe|msi|dmg|pkg|zip|rar|7z|iso|js|vbs|bat|cmd|scr|apk|jar|docm|xlsm|pptm|html?\.)$", re.I)
LOGIN_WORDS = re.compile(r"\b(sign in|log ?in|password|verify your account|confirm your identity|ssn|social security|"
                         r"card number|cvv|routing number|gift card|wire transfer|urgent payment)\b", re.I)


def reg_domain(host):
    """Approximate registrable domain without a public-suffix list."""
    parts = host.split(".")
    # US school districts: <district>.k12.<state>.us
    if len(parts) >= 4 and parts[-1] == "us" and parts[-3] == "k12":
        return ".".join(parts[-4:])
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in ("co", "com", "org", "net", "gov", "edu", "ac"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check(url, anchor=""):
    """Return (verdict, reasons). Pure function, no network."""
    reasons = []
    try:
        u = urllib.parse.urlsplit(url.strip())
        port = u.port
    except Exception:
        return "fail", ["unparseable"]
    if u.scheme in ("mailto", "tel", "sms"):
        return "skip", [u.scheme]
    if u.scheme != "https":
        reasons.append(f"scheme {u.scheme or 'none'} (https only)")
    host = (u.hostname or "").lower().rstrip(".")
    if not host:
        return "fail", ["no host"]
    if "@" in (u.netloc or ""):
        reasons.append("userinfo in URL (user@host trick)")
    if port not in (None, 443):
        reasons.append(f"non-standard port {port}")
    try:
        ipaddress.ip_address(host)
        reasons.append("raw IP address host")
    except ValueError:
        pass
    if "xn--" in host:
        reasons.append("punycode host (lookalike characters)")
    if not re.fullmatch(r"[a-z0-9.-]+", host):
        reasons.append("non-ASCII host")
    if host.count(".") >= 5:
        reasons.append("deeply nested subdomains")
    tld = host.rsplit(".", 1)[-1]
    if tld in RISKY_TLDS:
        reasons.append(f"high-abuse TLD .{tld}")
    if any(host == s or host.endswith("." + s) for s in RISKY_SUFFIXES):
        reasons.append("free/instant hosting often used for phishing")
    if DOWNLOAD_EXT.search(u.path or ""):
        reasons.append("direct download of an executable/archive/macro file")
    if len(url) > 2000:
        reasons.append("very long URL")
    rd = reg_domain(host)
    label = rd.split(".")[0]
    squashed = host.replace("-", "").translate(str.maketrans("013457", "oleast")).replace("rn", "m").replace("vv", "w")
    for b in BRANDS:
        if any(host == o or host.endswith("." + o) for o in OFFICIAL.get(b, [])):
            continue
        if (b in squashed and b not in NO_SUBSTRING_MATCH) or (0 < lev(label, b) <= 2 and len(label) >= 5):
            reasons.append(f"looks like {b} but is {rd}")
    # Visible text that is itself a URL/domain pointing somewhere else.
    a = (anchor or "").strip().lower()
    m = re.search(r"(?:https?://)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)", a)
    if m and "." in m.group(1) and not a.startswith("@"):
        shown = m.group(1)
        if reg_domain(shown) != rd and not host.endswith(shown):
            reasons.append(f"link text shows {shown} but goes to {rd}")
    if reasons:
        return "fail", reasons
    low = url.lower()
    if any(h == host or host.endswith("." + h) for h in SKIP_HOSTS):
        return "skip", ["social/app-store link"]
    if any(w in low for w in SKIP_WORDS) or any(w in a for w in ("unsubscribe", "privacy")):
        return "skip", ["unsubscribe/preferences link"]
    if re.search(r"\.(png|jpe?g|gif|webp|svg|ico)(\?|$)", u.path or "", re.I):
        return "skip", ["image"]
    return "pass", []


class _Hops(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.hops = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if len(self.hops) >= MAX_HOPS:
            raise urllib.error.HTTPError(newurl, code, "too many redirects", headers, fp)
        v, r = check(newurl)
        self.hops.append(newurl)
        if v != "pass":
            raise urllib.error.HTTPError(newurl, code, "redirect blocked: " + "; ".join(r or [v]), headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _gdoc_export(url):
    m = re.match(r"https://docs\.google\.com/(document|presentation|spreadsheets)/d/([A-Za-z0-9_-]+)", url)
    if not m:
        return url
    kind, did = m.groups()
    fmt = {"document": "txt", "presentation": "txt", "spreadsheets": "csv"}[kind]
    return f"https://docs.google.com/{kind}/d/{did}/export?format={fmt}"


def to_text(raw, ctype):
    t = raw.decode("utf-8", "replace")
    if "html" in ctype:
        t = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
        t = re.sub(r"<br\s*/?>|</(p|div|li|tr|h[1-6])>", "\n", t, flags=re.I)
        t = htmlmod.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t ]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def fetch(url):
    """Follow a link that passed check(). Returns dict with final url, text or error."""
    target = _gdoc_export(url)
    hops = _Hops()
    opener = urllib.request.build_opener(hops)  # no cookie processor: anonymous
    req = urllib.request.Request(target, headers={"User-Agent": UA, "Accept": "text/html,text/plain,text/csv"})
    try:
        with opener.open(req, timeout=20) as r:
            ctype = r.headers.get("Content-Type", "").lower()
            final = r.geturl()
            if not any(k in ctype for k in ("text/html", "text/plain", "text/csv")):
                return {"final": final, "error": f"not a text page ({ctype or 'unknown type'}), not read"}
            raw = r.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        return {"final": hops.hops[-1] if hops.hops else target, "error": f"HTTP {e.code}: {e.msg}"[:200]}
    except Exception as e:
        return {"final": target, "error": str(e)[:200]}
    text = to_text(raw[:MAX_BYTES], ctype)
    out = {"final": final, "hops": hops.hops, "text": text[:MAX_CHARS], "truncated": len(text) > MAX_CHARS}
    if re.search(r"accounts\.google\.com|/signin|/login", final, re.I) or (
            len(text) < 3000 and LOGIN_WORDS.search(text)):
        out["login_or_payment_page"] = True
    return out


def extract_links(plain_parts, html_parts):
    """[(url, anchor_text)] in document order, deduped."""
    seen, out = set(), []
    for h in html_parts:
        for m in re.finditer(r"<a\b[^>]*?href\s*=\s*[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", h, re.S | re.I):
            href = htmlmod.unescape(m.group(1)).strip()
            anchor = re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
            if href not in seen:
                seen.add(href)
                out.append((href, anchor[:200]))
    for p in plain_parts:
        for m in re.finditer(r"https?://[^\s<>\"')\]]+", htmlmod.unescape(p)):
            href = m.group(0).rstrip(".,;")
            if href not in seen:
                seen.add(href)
                out.append((href, ""))
    return out


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def resolve_wrapped(url, anchor):
    """Click-tracker links (mass-mail services wrap every link in an http://
    tracker whose visible text is the real address). Walk the redirect chain
    WITHOUT reading any page, and accept only if the final URL passes check()
    and lands on the same domain the link text showed. Returns final URL or None."""
    m = re.search(r"(?:https?://)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)", (anchor or "").lower())
    if not m:
        return None
    shown = reg_domain(m.group(1))
    opener = urllib.request.build_opener(_NoRedirect())
    cur = url
    for _ in range(MAX_HOPS):
        try:
            with opener.open(urllib.request.Request(cur, headers={"User-Agent": UA}), timeout=15):
                break  # 2xx: no more redirects
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location") if e.code in (301, 302, 303, 307, 308) else None
            if not loc:
                return None
            cur = urllib.parse.urljoin(cur, loc)
        except Exception:
            return None
    if cur == url:
        return None
    v, _ = check(cur)
    host = (urllib.parse.urlsplit(cur).hostname or "").lower()
    if v == "pass" and reg_domain(host) == shown:
        return cur
    return None


def analyze(links):
    """Check every link, follow the ones that pass (up to MAX_LINKS fetches)."""
    results, fetched = [], 0
    for url, anchor in links:
        v, reasons = check(url, anchor)
        if any(w in (url + " " + anchor).lower() for w in SKIP_WORDS):
            v, reasons = "skip", ["unsubscribe/preferences link"]
        rec = {"url": url[:500], "anchor": anchor, "verdict": v, "reasons": reasons}
        # Only these two signals are typical of a legit click-tracker; anything else stays failed.
        if v == "fail" and all(r.startswith(("scheme http ", "link text shows")) for r in reasons):
            final = resolve_wrapped(url, anchor)
            if final:
                rec["tracker_resolved_to"] = final
                url, v, rec["verdict"], rec["reasons"] = final, "pass", "pass", ["click-tracker resolved to the shown domain"]
        if v == "pass":
            if fetched >= MAX_LINKS:
                rec["verdict"], rec["reasons"] = "skip", ["link limit reached"]
            else:
                fetched += 1
                rec.update(fetch(url))
                if "error" in rec and "redirect blocked" in rec["error"]:
                    rec["verdict"], rec["reasons"] = "fail", [rec["error"]]
        results.append(rec)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    verdict, why = check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
    print(json.dumps({"verdict": verdict, "reasons": why}))
