#!/bin/bash
# ---------------------------------------------------------------------------
# agent-session.sh: launchd-supervised launcher for a long-lived Claude Code
# session in this workspace (see launchd/agent-session.plist).
#
# WHY: the whole system hangs off long-lived `claude` processes, and
# session-scoped crons are not persisted to disk. If the process dies, the
# heartbeat dies with it and nothing restarts it. An agent that goes silently
# dark for days while its principal is away is the failure this prevents.
#
# WHAT IT DOES:
#   1. Auto-restart: launchd (KeepAlive) relaunches this when claude exits. On
#      each fresh start the SessionStart hook (scripts/session-start.py) tells
#      the session to rebuild its heartbeat cron.
#   2. No interactive /login: if a Keychain slot holds an Anthropic API key
#      (session.api_key_keychain_service, default "<short>/anthropic-api",
#      account = workspace.os_user), it is exported into the environment. With
#      no key stored, claude uses its normal login.
#
# Design notes:
#   * --continue, not bare --resume: bare --resume opens an interactive picker,
#     which would hang forever under launchd (no keyboard).
#   * `script -q /dev/null ...`: launchd has no controlling terminal, but the
#     interactive session wants a TTY. macOS's built-in `script` attaches it to
#     a pseudo-tty (typescript discarded). No tmux dependency.
#   * session.channels in config (e.g. a channel plugin) is passed as
#     --channels when set.
# ---------------------------------------------------------------------------
set -uo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
HERE="$(cd "$(dirname "$0")" && pwd)"
CFG="$(python3 "$HERE/messages_config.py" --session)" || { echo "FATAL: cannot read config/workspace.json" >&2; exit 1; }
eval "$CFG"

KEY="$(security find-generic-password -s "$KC_API_SERVICE" -a "$KC_ACCOUNT" -w 2>/dev/null || true)"
if [ -n "$KEY" ]; then
  export ANTHROPIC_API_KEY="$KEY"
else
  echo "$(date '+%Y-%m-%dT%H:%M:%S%z') note: no API key in Keychain slot $KC_API_SERVICE; using claude's own login" >&2
fi
unset KEY

cd "$WORKDIR" || { echo "FATAL: cannot cd to $WORKDIR" >&2; exit 1; }
echo "$(date '+%Y-%m-%dT%H:%M:%S%z') launching $AGENT_NAME session (--continue) under pty" >&2

ARGS=(--continue --dangerously-skip-permissions)
[ -n "$SESSION_CHANNELS" ] && ARGS+=(--channels "$SESSION_CHANNELS")

# exec so launchd supervises `script` (and thus claude) directly. When claude
# exits, script exits, this wrapper exits, and launchd relaunches.
exec script -q /dev/null "$CLAUDE" "${ARGS[@]}"
