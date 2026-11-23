#!/usr/bin/env python3
"""Print the messaging-bridge and session-launcher settings as shell assignments.

The shell launchers run `eval "$(python3 scripts/messages_config.py)"` so that
every value comes from config/workspace.json and nothing personal is baked into
a script. Values are shell-quoted. Exits non-zero (and prints nothing to eval)
if a required value is missing, so a half-configured bridge never starts.

Usage:
  messages_config.py            bridge settings (requires messages.channel_plugin)
  messages_config.py --session  launcher settings only (no channel required)
"""

import json
import os
import re
import shlex
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402


OUT = []


def emit(name, value):
    OUT.append(f"{name}={shlex.quote(str(value))}")


def main():
    session_only = "--session" in sys.argv[1:]
    home = os.path.expanduser("~")
    claude = wc.get("workspace.claude_path") or shutil.which("claude") or os.path.join(home, ".local/bin/claude")
    emit("WORKDIR", wc.ROOT)
    emit("CLAUDE", claude)
    emit("AGENT_NAME", wc.agent_name())
    emit("AGENT_SLUG", wc.agent_short().lower())
    emit("KC_ACCOUNT", wc.keychain_account())
    emit("KC_API_SERVICE", wc.get("session.api_key_keychain_service") or wc.keychain_service("anthropic-api"))
    emit("SESSION_CHANNELS", wc.get("session.channels") or "")
    if session_only:
        return 0

    m = wc.get("messages", {}) or {}
    plugin = (m.get("channel_plugin") or "").strip()
    if not plugin:
        print("messages.channel_plugin is not set in config/workspace.json; bridge disabled", file=sys.stderr)
        return 2
    sid = (m.get("session_id") or "").strip()
    if not sid:
        print("messages.session_id is not set in config/workspace.json", file=sys.stderr)
        return 2
    project_dir = os.path.join(home, ".claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", str(wc.ROOT)))
    deny = []
    for p in m.get("deny_read_paths") or ["~/Library/Messages/**"]:
        absolute = os.path.expanduser(p)
        deny += [f"Read(/{absolute})", f"Edit(/{absolute})"]  # leading // = absolute path rule
    settings = {
        "enabledPlugins": m.get("enabled_plugins") or {},
        "permissions": {"deny": deny},
        "sandbox": {"enabled": True, "allowUnsandboxedCommands": False},
    }
    emit("SESSION_NAME", m.get("session_name") or f"{wc.agent_name()} Messages")
    emit("SESSION_ID", sid)
    emit("CHANNEL_PLUGIN", plugin)
    emit("DEV_CHANNEL", "1" if m.get("dev_channel") else "0")
    emit("SERVER_PATTERN", m.get("server_pattern") or "")
    emit("PROJECT_DIR", project_dir)
    emit("RUNLOG", os.path.join(home, "Library", "Logs", f"{wc.agent_short().lower()}-messages.log"))
    emit("SETTINGS_JSON", json.dumps(settings, separators=(",", ":")))
    for k, v in (m.get("env") or {}).items():
        if k.isidentifier():
            OUT.append(f"export {k}={shlex.quote(str(v))}")
    return 0


if __name__ == "__main__":
    rc = main()
    if rc == 0:
        print("\n".join(OUT))  # all or nothing: never hand eval a partial config
    sys.exit(rc)
