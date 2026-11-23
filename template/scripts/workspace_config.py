#!/usr/bin/env python3
"""Shared runtime config for every workspace script.

All personal values (names, addresses, timezone, quiet hours, sender lists)
live in config/workspace.json, written by bin/init_workspace.py. Scripts import
this module instead of hardcoding anything:

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import workspace_config as wc
    cfg = wc.load()
    wc.ROOT, wc.tz(), wc.agent_name(), ...

The workspace root is the parent of this scripts/ folder, so the workspace can
be moved without editing anything. AGENT_WORKSPACE overrides it (tests).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(os.environ.get("AGENT_WORKSPACE") or Path(__file__).resolve().parent.parent)
CONFIG_FILE = ROOT / "config" / "workspace.json"
MEMORY = ROOT / "memory"
STATE_FILE = MEMORY / "heartbeat-state.json"

# The heartbeat cron prompt. Hooks recognise heartbeat turns by this substring,
# so it must match the prompt the Ops session's cron sends.
HEARTBEAT_MARKER = "HEARTBEAT.md if it exists"
HEARTBEAT_PROMPT = (
    "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. "
    "Do not infer or repeat old tasks from prior chats. If nothing needs "
    "attention, reply HEARTBEAT_OK."
)

_cache = None


def load():
    """Return the parsed workspace.json, or {} if it is missing or unreadable.

    Hooks must never crash a session, so a missing config degrades to defaults.
    Scripts that cannot run safely without config (email send, inbox filter)
    check the specific keys they need and refuse.
    """
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(CONFIG_FILE.read_text())
        except Exception:
            _cache = {}
    return _cache


def get(path, default=None):
    """Dotted lookup: get("comms.quiet_hours_start", 20)."""
    node = load()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def agent_name():
    return get("agent.name", "Agent")


def agent_short():
    return get("agent.short", "AGT")


def principal_name():
    return get("principal.name", "the principal")


def tz():
    try:
        return ZoneInfo(get("principal.timezone", "UTC"))
    except Exception:
        return ZoneInfo("UTC")


def now():
    return datetime.now(tz())


def now_iso():
    return now().isoformat(timespec="seconds")


def quiet_hours():
    """(start, end) local hours. Outbound is allowed from end until start."""
    return int(get("comms.quiet_hours_start", 20)), int(get("comms.quiet_hours_end", 9))


def in_quiet_hours(at=None):
    start, end = quiet_hours()
    h = (at or now()).hour
    if start == end:
        return False
    if start > end:  # wraps midnight, e.g. 20 -> 9
        return h >= start or h < end
    return start <= h < end


def trusted_senders():
    return [s.strip().lower() for s in get("comms.trusted_senders", []) if isinstance(s, str) and s.strip()]


def trusted_emails():
    return [s for s in trusted_senders() if "@" in s]


def trusted_phones():
    return [s for s in trusted_senders() if s.startswith("+")]


def keychain_account():
    return get("workspace.os_user") or os.environ.get("USER", "")


def keychain_service(purpose):
    """Keychain service name convention: <short-lowercase>/<purpose>."""
    return f"{agent_short().lower()}/{purpose}"
