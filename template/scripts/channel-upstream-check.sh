#!/bin/bash
# Daily upstream check for a locally forked channel plugin (optional).
#
# If the Messages bridge runs a strict local fork of a marketplace channel
# plugin, upstream fixes must still be folded in by hand. This refreshes the
# marketplace, then diffs the official plugin against the pristine snapshot the
# fork was built from (plugins/upstream/<plugin>-<ver>). Prints exactly one
# status line first:
#   UPSTREAM_UNCHANGED <ver>
#   UPSTREAM_CHANGED <snapshot-ver> -> <new-ver> (<n> files)   + diff in plugins/upstream/pending.diff
#   UPSTREAM_ERROR <reason>
# Ops runs this daily. It never edits the fork. Folding a change in is a
# reviewed change by Admin: patch the fork, run its tests, refresh the snapshot,
# restart the Messages session.
#
# Config (config/workspace.json):
#   messages.upstream_plugin       plugin dir name upstream, e.g. "imessage"
#   messages.upstream_marketplace  default "claude-plugins-official"
#   messages.upstream_subdir       default "external_plugins"
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
read_cfg() { python3 -c "import sys; sys.path.insert(0, sys.argv[1]); import workspace_config as w; print(w.get(sys.argv[2], sys.argv[3]) or sys.argv[3])" "$HERE" "$1" "$2"; }
PLUGIN="$(read_cfg messages.upstream_plugin '')"
[ -n "$PLUGIN" ] || { echo "UPSTREAM_ERROR messages.upstream_plugin not set"; exit 1; }
MKT_NAME="$(read_cfg messages.upstream_marketplace claude-plugins-official)"
SUBDIR="$(read_cfg messages.upstream_subdir external_plugins)"
CLAUDE="$(command -v claude || echo "$HOME/.local/bin/claude")"

MKT="$HOME/.claude/plugins/marketplaces/$MKT_NAME"
UP="$MKT/$SUBDIR/$PLUGIN"
SNAP_DIR="$REPO/plugins/upstream"
SNAP=$(ls -d "$SNAP_DIR/$PLUGIN"-* 2>/dev/null | sort -V | tail -1)
[ -n "$SNAP" ] || { echo "UPSTREAM_ERROR no snapshot in $SNAP_DIR"; exit 1; }

"$CLAUDE" plugin marketplace update "$MKT_NAME" >/dev/null 2>&1 \
  || git -C "$MKT" pull --ff-only -q >/dev/null 2>&1 \
  || { echo "UPSTREAM_ERROR could not refresh marketplace"; exit 1; }
[ -d "$UP" ] || { echo "UPSTREAM_ERROR $UP missing (plugin removed or renamed upstream?)"; exit 1; }

ver() { python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'])" "$1/.claude-plugin/plugin.json" 2>/dev/null || echo "?"; }
SV=$(ver "$SNAP"); UV=$(ver "$UP")
DIFF=$(diff -ru -x node_modules -x .in_use -x skills "$SNAP" "$UP")
if [ -z "$DIFF" ]; then
  rm -f "$SNAP_DIR/pending.diff"
  echo "UPSTREAM_UNCHANGED $SV"
else
  printf '%s\n' "$DIFF" > "$SNAP_DIR/pending.diff"
  N=$(diff -rq -x node_modules -x .in_use -x skills "$SNAP" "$UP" | wc -l | tr -d ' ')
  echo "UPSTREAM_CHANGED $SV -> $UV ($N files)"
  diff -rq -x node_modules -x .in_use -x skills "$SNAP" "$UP"
fi
