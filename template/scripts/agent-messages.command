#!/bin/bash
# ---------------------------------------------------------------------------
# agent-messages.command: runs the Messages session (the text-message front door).
#
# Run it in Terminal.app, and grant Terminal.app Full Disk Access, so the
# messaging channel plugin's server can read ~/Library/Messages/chat.db.
# Double-click it, or:
#   open -a Terminal <workspace>/scripts/agent-messages.command
#
# Every value comes from config/workspace.json via scripts/messages_config.py:
#   messages.channel_plugin   e.g. plugin:imessage@claude-plugins-official, or a
#                             local strict fork such as plugin:imessage-strict@local
#   messages.dev_channel      true for a local fork (loads it as a development
#                             channel; agent-messages-run.exp answers the warning)
#   messages.enabled_plugins  {"<plugin>@<marketplace>": true, ...} for this session only
#   messages.session_id       fixed UUID so restarts resume the same conversation
#
# Safety:
# - The model is denied Read/Edit on ~/Library/Messages and runs with the Bash
#   sandbox on and no unsandboxed escape. Only the plugin's server reads chat.db.
# - The plugin must enforce the sender allowlist (comms.trusted_senders) in code
#   before any message reaches the model. Use a strict fork if the stock plugin
#   does not.
# - Install the channel plugin DISABLED user-wide; only this session enables it.
#
# Loops: if claude exits, it relaunches after 10s. Ctrl-C twice to stop.
# ---------------------------------------------------------------------------
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CFG="$(python3 "$HERE/messages_config.py")" || { echo "Messages bridge not configured; see docs/scripts.md"; exit 1; }
eval "$CFG"

PROMPT_FILE="$WORKDIR/scripts/agent-messages-prompt.md"
cd "$WORKDIR" || { echo "cannot cd to $WORKDIR"; exit 1; }
printf '\033]0;%s\007' "$SESSION_NAME"

if [ "$DEV_CHANNEL" = "1" ]; then
  CHANNEL_ARGS=(--dangerously-load-development-channels "$CHANNEL_PLUGIN")
else
  CHANNEL_ARGS=(--channels "$CHANNEL_PLUGIN")
fi

while true; do
  if [ -f "$PROJECT_DIR/$SESSION_ID.jsonl" ]; then
    SESSION_ARGS=(--resume "$SESSION_ID")
  else
    SESSION_ARGS=(--session-id "$SESSION_ID")
  fi
  echo "$(date -Iseconds) start ${SESSION_ARGS[0]}" | tee -a "$RUNLOG"
  /usr/bin/expect -f "$WORKDIR/scripts/agent-messages-run.exp" "$CLAUDE" "${SESSION_ARGS[@]}" \
    --name "$SESSION_NAME" \
    "${CHANNEL_ARGS[@]}" \
    --settings "$SETTINGS_JSON" \
    --append-system-prompt "$(cat "$PROMPT_FILE")" \
    --dangerously-skip-permissions \
    "Session (re)started by the launcher. Run the catch-up from your instructions now (read recent messages and compare with the last logged message ids), handle anything missed, then wait for texts."
  rc=$?
  echo "$(date -Iseconds) exit rc=$rc; restarting in 10s" | tee -a "$RUNLOG"
  sleep 10
done
