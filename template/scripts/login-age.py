#!/usr/bin/env python3
"""Report Claude Code login age for a periodic re-login reminder.

Interactive Claude Code logins expire after roughly four weeks. A long-running
Ops session that loses its login goes dark until a human runs /login, so the
heartbeat calls this and reminds the principal a couple of days early.

Reads the most recent /login from ~/.claude/history.jsonl (epoch ms) and prints
JSON: last_login, age_days, next_reminder (last_login + N*step that is due or
upcoming), and due (true when a step has passed that has not been stamped in
memory/heartbeat-state.json lastChecks.login_reminder).

history.jsonl is only flushed when a session exits, so a /login run inside a
long-lived session is invisible until restart. The agent can stamp it by hand in
lastChecks.login_manual (epoch seconds); the newer of the two wins.

Config (config/workspace.json, optional):
  heartbeat.login_reminder_days   default 25
  heartbeat.login_expiry_days     default 27.5 (measured; adjust to yours)
"""

import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

HISTORY = os.path.expanduser("~/.claude/history.jsonl")
STEP = timedelta(days=float(wc.get("heartbeat.login_reminder_days", 25)))
EXPIRY = timedelta(days=float(wc.get("heartbeat.login_expiry_days", 27.5)))


def lastchecks():
    try:
        return json.loads(wc.STATE_FILE.read_text()).get("lastChecks", {})
    except (OSError, ValueError):
        return {}


def main():
    tz = wc.tz()
    last = None
    try:
        with open(HISTORY) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if str(d.get("display", "")).strip().startswith("/login"):
                    ts = d.get("timestamp")
                    if isinstance(ts, (int, float)):
                        t = datetime.fromtimestamp(ts / 1000, tz)
                        if last is None or t > last:
                            last = t
    except OSError:
        pass

    checks = lastchecks()
    manual = checks.get("login_manual")
    if isinstance(manual, (int, float)):
        m = datetime.fromtimestamp(manual, tz)
        if last is None or m > last:
            last = m

    if last is None:
        print(json.dumps({"error": "no /login found in history and no lastChecks.login_manual stamp"}))
        return

    now = datetime.now(tz)
    age = now - last
    n = int(age / STEP)
    latest_due = last + n * STEP if n >= 1 else None
    stamped = checks.get("login_reminder")
    stamped_dt = datetime.fromtimestamp(stamped, tz) if isinstance(stamped, (int, float)) else None
    due = latest_due is not None and (stamped_dt is None or stamped_dt < latest_due)
    print(json.dumps({
        "last_login": last.isoformat(timespec="minutes"),
        "age_days": round(age.total_seconds() / 86400, 2),
        "increments_passed": n,
        "due": due,
        "latest_due": latest_due.isoformat(timespec="minutes") if latest_due else None,
        "next_reminder": (last + (n + 1) * STEP).isoformat(timespec="minutes"),
        "est_expiry": (last + EXPIRY).isoformat(timespec="minutes"),
    }))


if __name__ == "__main__":
    main()
