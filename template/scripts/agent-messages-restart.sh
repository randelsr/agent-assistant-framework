#!/bin/bash
# Restart the Messages session cleanly.
#
# Lesson: plain `kill` (SIGTERM) does not stop the claude TUI or its expect
# wrapper, so naive restarts can leave several live Messages sessions side by
# side, all answering the same texts. Order matters: stop the launcher loop
# first so it can't respawn, then expect, then claude, then the channel
# server. Escalate to SIGKILL. Verifies exactly one instance afterwards.
# Prints OK or FAIL.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CFG="$(python3 "$HERE/messages_config.py")" || { echo "FAIL bridge not configured"; exit 1; }
eval "$CFG"

pids() { [ -n "$1" ] && pgrep -f "$1" | tr '\n' ' '; }
stop() { # $1 pattern
  local p; p=$(pids "$1"); [ -z "${p// /}" ] && return
  kill $p 2>/dev/null; sleep 2
  p=$(pids "$1"); [ -n "${p// /}" ] && kill -9 $p 2>/dev/null
}
stop "scripts/agent-messages.command"
stop "agent-messages-run.exp"
stop "name $SESSION_NAME"
[ -n "$SERVER_PATTERN" ] && stop "$SERVER_PATTERN"
sleep 1
left="$(pids "name $SESSION_NAME")"
[ -n "$SERVER_PATTERN" ] && left="$left$(pids "$SERVER_PATTERN")"
[ -n "${left// /}" ] && { echo "FAIL could not stop: $left"; exit 1; }

open -a Terminal "$WORKDIR/scripts/agent-messages.command"
s=0; c=0
for i in $(seq 1 30); do
  sleep 2
  c=$(pgrep -f "name $SESSION_NAME" | wc -l | tr -d ' ')
  if [ -n "$SERVER_PATTERN" ]; then
    s=$(pgrep -f "$SERVER_PATTERN" | wc -l | tr -d ' ')
  else
    s=1
  fi
  # one claude + one expect match "name <session>"
  if [ "$s" = 1 ] && [ "$c" = 2 ]; then echo "OK one instance"; exit 0; fi
done
echo "FAIL after 60s: servers=$s sessions=$c"; exit 1
