#!/usr/bin/env python3
"""Deterministic heartbeat state stamp (UserPromptSubmit hook).

Runs on every prompt. Returns early unless the prompt is the heartbeat poll
(UserPromptSubmit hooks ignore the settings.json `matcher`, so the filter has
to live here; otherwise the principal's own messages would keep
lastHeartbeatFire fresh and blind the liveness check).

On a heartbeat prompt it updates lastUpdated (ISO 8601, configured TZ) and
lastHeartbeatFire (Unix epoch) in memory/heartbeat-state.json. All other fields
are preserved.

Hardening (each from a real incident):
  - Corrupt state is never silently reset. The bad bytes are kept for
    forensics and the last known-good backup is restored.
  - A backup is rolled forward before every write, and writes are atomic
    (temp file + rename), so a reader never sees a half-written file.
  - Outage detection: a gap of more than 15 min since the previous fire, or
    more than 30 min since the last heartbeat turn that actually COMPLETED
    (lastOpsTurnOk, stamped by ops-turn-ok.py), records pendingRecovery so
    Ops runs its catch-up step. Measuring completed turns matters: a cron can
    keep firing while every model turn behind it fails.

Exit 0 unconditionally; never block the heartbeat on a stamp failure.
"""

import json
import os
import sys
from datetime import datetime
from time import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

STATE_FILE = wc.STATE_FILE
BACKUP_FILE = STATE_FILE.with_name(".heartbeat-state.json.bak")
FIRE_GAP = 15 * 60
OK_GAP = 30 * 60


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        payload = {}
    if wc.HEARTBEAT_MARKER not in str(payload.get("prompt", "")):
        return

    now_epoch = int(time())
    now_iso = wc.now_iso()

    state = {}
    if STATE_FILE.exists():
        raw = STATE_FILE.read_text()
        try:
            state = json.loads(raw)
        except Exception:
            stamp = wc.now().strftime("%Y%m%dT%H%M%S")
            try:
                STATE_FILE.with_name(f".heartbeat-state.corrupt.{stamp}.json").write_text(raw)
            except Exception:
                pass
            if BACKUP_FILE.exists():
                try:
                    state = json.loads(BACKUP_FILE.read_text())
                except Exception:
                    state = {}

    prev = state.get("lastHeartbeatFire")
    ok = state.get("lastOpsTurnOk")
    gap_from = None
    if isinstance(prev, (int, float)) and now_epoch - prev > FIRE_GAP:
        gap_from = int(prev)
    if isinstance(ok, (int, float)) and now_epoch - ok > OK_GAP:
        gap_from = min(gap_from, int(ok)) if gap_from else int(ok)
    if gap_from is not None:
        pending = state.get("pendingRecovery") or {}
        start = pending.get("gapStartEpoch", gap_from)
        state["pendingRecovery"] = {
            "gapStartEpoch": start,
            "gapStart": datetime.fromtimestamp(start, wc.tz()).isoformat(timespec="seconds"),
            "gapEnd": now_iso,
            "gapMinutes": round((now_epoch - start) / 60),
        }

    state["lastUpdated"] = now_iso
    state["lastHeartbeatFire"] = now_epoch

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists() and state:
        try:
            BACKUP_FILE.write_text(STATE_FILE.read_text())
        except Exception:
            pass
    tmp = STATE_FILE.with_name(f".heartbeat-state.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    os.replace(tmp, STATE_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
