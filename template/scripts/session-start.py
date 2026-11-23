#!/usr/bin/env python3
"""SessionStart hook: stamp state + inject session-role / cron context.

Two responsibilities:
1. Deterministically stamp memory/heartbeat-state.json with
   lastSessionStart (Unix epoch) and lastUpdated (ISO 8601, configured TZ).
   Does NOT bump lastHeartbeatFire: a session start is not a heartbeat fire,
   and conflating the two would mask a broken heartbeat.
2. Emit hookSpecificOutput JSON with additionalContext that tells the Ops
   session to verify its cron fleet via CronList and recreate the heartbeat
   if missing, and tells every other session to create none.

This is the durability backstop for session-scoped crons, which do not
survive a Claude Code restart and expire after several days.

Roles (one workspace, several long-lived sessions):
  <Agent> Ops    runs the heartbeat cron and every scheduled dispatch.
  <Agent> Admin  the principal's conversation thread. Runs no crons.
  thread agents  (claude --agent <slug>) run no crons.
A session learns its role from its first prompt ("You are <Agent> Ops.").
"""

import json
import os
import sys
from time import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

HEARTBEAT_CRON = "0,5,10,15,20,25,30,35,40,45,50,55 * * * *"


def context():
    name, who = wc.agent_name(), wc.principal_name()
    cron = wc.get("heartbeat.cron", HEARTBEAT_CRON)
    return (
        f"SESSION START ({name} workspace).\n\n"
        f"Architecture: the heartbeat cron and every scheduled dispatch run ONLY in the "
        f"{name} Ops session. {name} Admin is {who}'s conversation thread and runs no crons. "
        f"Thread agents (claude --agent <slug>) and desktop scheduled-task runs create no crons.\n\n"
        f"If THIS session is {name} Ops (its prompt says so): run CronList and recreate the "
        f"heartbeat if missing via CronCreate ({cron}, recurring) with prompt "
        f"\"{wc.HEARTBEAT_PROMPT}\" Delete any duplicate heartbeat crons.\n\n"
        f"Every other session: create no crons, delete none. If you are {name} Admin and "
        f"CronList shows a heartbeat cron in THIS session, delete it (it belongs to {name} Ops).\n\n"
        "Do NOT treat this as a heartbeat fire."
    )


def stamp_state():
    state = {}
    if wc.STATE_FILE.exists():
        try:
            state = json.loads(wc.STATE_FILE.read_text())
        except Exception:
            return  # heartbeat-stamp.py owns corrupt-file recovery; never clobber here
    state["lastUpdated"] = wc.now_iso()
    state["lastSessionStart"] = int(time())
    try:
        wc.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = wc.STATE_FILE.with_name(f".heartbeat-state.{os.getpid()}.ss.tmp")
        tmp.write_text(json.dumps(state, indent=2) + "\n")
        os.replace(tmp, wc.STATE_FILE)
    except Exception:
        pass


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass
    stamp_state()
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": context()}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
