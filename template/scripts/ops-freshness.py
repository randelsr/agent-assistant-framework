#!/usr/bin/env python3
"""UserPromptSubmit hook: warn the Admin session when the Ops heartbeat is stale.

Reads memory/heartbeat-state.json. If the prompt is not itself a heartbeat poll
and either
  - the last heartbeat fire is older than 15 minutes, or
  - the cron is firing but the last COMPLETED heartbeat turn (lastOpsTurnOk,
    from ops-turn-ok.py) is older than 30 minutes,
inject context telling Admin to tell the principal in one line and restart or
nudge Ops. Silent otherwise. Exit 0 always.

A fresh fire is not proof of life: a cron can keep firing while every model turn
behind it fails (for example on API connection errors).
"""

import json
import os
import sys
from time import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

STALE_SECONDS = 15 * 60


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        payload = {}
    if wc.HEARTBEAT_MARKER in str(payload.get("prompt", "")):
        return
    try:
        st = json.loads(wc.STATE_FILE.read_text())
    except Exception:
        return  # no heartbeat has ever run; nothing to compare against
    name, who = wc.agent_name(), wc.principal_name()
    now = int(time())
    fire_age = now - int(st.get("lastHeartbeatFire", 0) or 0)
    ok = st.get("lastOpsTurnOk")
    ok_age = now - int(ok) if isinstance(ok, (int, float)) else None
    if fire_age > STALE_SECONDS:
        msg = (
            f"OPS LIVENESS WARNING: the {name} Ops heartbeat last fired {fire_age // 60} min ago "
            f"(threshold 15). Only {name} Admin acts on this; thread agents ignore it. {name} Admin: "
            f"tell {who} in one line, then restart {name} Ops (message the Ops session; if it no "
            "longer exists, start a new one per HEARTBEAT.md)."
        )
    elif ok_age is not None and ok_age > 2 * STALE_SECONDS:
        msg = (
            f"OPS LIVENESS WARNING: the {name} Ops heartbeat is firing, but its last COMPLETED "
            f"heartbeat turn was {ok_age // 60} min ago (threshold 30). Its turns are likely "
            f"failing (e.g. API connection errors) or one turn is stuck. Only {name} Admin acts on "
            f"this. {name} Admin: tell {who} in one line, check the Ops session, and nudge it "
            "with a message if it is idle."
        )
    else:
        return
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": msg}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
