#!/usr/bin/env python3
"""Stop hook: stamp lastOpsTurnOk when a heartbeat turn actually completes.

Why: a heartbeat cron can keep firing every 5 minutes (so lastHeartbeatFire
stays fresh) while every model turn behind it fails with an API error. Without
this stamp, neither the outage-recovery check nor the Admin liveness warning
notices, because both would only measure cron fires, not completed work.

Runs when any turn ends, in every session in this workspace. Stamps only when
ALL of these hold:
  - the turn's prompt was the heartbeat poll, so only Ops turns count;
  - the turn's final assistant text is not an "API Error".
heartbeat-stamp.py and ops-freshness.py then measure the gap from this stamp.

Exit 0 always; never block a turn.
"""

import json
import os
import sys
from time import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

TAIL_BYTES = 2_000_000


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
    return ""


def last_turn(transcript):
    """Return (last real user prompt text, last assistant text after it)."""
    with open(transcript, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - TAIL_BYTES))
        lines = f.read().decode("utf-8", "replace").splitlines()
    assistant = None
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except Exception:
            continue
        msg = rec.get("message") or {}
        if rec.get("type") == "assistant" and assistant is None:
            t = text_of(msg.get("content"))
            if t.strip():
                assistant = t
        elif rec.get("type") == "user":
            c = msg.get("content")
            if isinstance(c, list) and any(isinstance(i, dict) and i.get("type") == "tool_result" for i in c):
                continue  # tool output, not a prompt
            t = text_of(c)
            if t.strip():
                return t, assistant or ""
    return "", assistant or ""


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return
    tp = payload.get("transcript_path")
    if not tp or not os.path.exists(tp):
        return
    prompt, answer = last_turn(tp)
    if wc.HEARTBEAT_MARKER not in prompt:
        return
    if answer.lstrip().startswith("API Error"):
        return
    try:
        state = json.loads(wc.STATE_FILE.read_text())
    except Exception:
        return  # never create or repair the file from here; heartbeat-stamp owns that
    state["lastOpsTurnOk"] = int(time())
    state["lastOpsTurnOkIso"] = wc.now_iso()
    tmp = wc.STATE_FILE.with_name(f".heartbeat-state.{os.getpid()}.ok.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    os.replace(tmp, wc.STATE_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
