#!/usr/bin/env python3
"""Dump a Claude Code session transcript into memory/conversations/YYYY-MM-DD.md.

Stop hook. Writes one file per local date present in the transcript, in the
principal's configured IANA timezone (principal.timezone in
config/workspace.json; DST is handled by zoneinfo). Each file is rewritten in
full each run, so re-running with a longer transcript produces a longer file.

Rolling retention: files older than conversations.retention_days (default 7)
are deleted. memory/conversations/ is gitignored; it holds verbatim chat.

Several sessions share the workspace. Each run writes only the dates present in
its own transcript, so a busy day with two sessions keeps the most recent
writer's view. Treat these logs as a recovery aid, not a ledger.

Usage:
    log-conversation.py <transcript.jsonl>   explicit path
    log-conversation.py                      read transcript_path from stdin JSON
                                             (Claude Code Stop-hook contract)
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

CONVO_DIR = wc.MEMORY / "conversations"
LOCAL_TZ = wc.tz()
RETENTION_DAYS = int(wc.get("conversations.retention_days", 7))
SIG_KEYS = ("file_path", "command", "url", "skill", "query", "subject", "description", "prompt")


def parse_timestamp(ts: str) -> datetime:
    """Parse '2026-05-05T02:49:00.297Z' into a local, DST-aware datetime."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(LOCAL_TZ)


def render_user(msg: dict) -> str:
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append(block.get("text", ""))
            elif btype == "tool_result":
                marker = "tool_error" if block.get("is_error", False) else "tool_result"
                parts.append(f"`<{marker} for {str(block.get('tool_use_id', '?'))[:8]}>`")
            elif btype == "image":
                parts.append("`<image>`")
            else:
                parts.append(f"`<{btype}>`")
        return "\n\n".join(p for p in parts if p)
    return ""


def render_assistant(msg: dict):
    """Return (text_content, list_of_tool_call_signatures). Thinking is skipped."""
    content = msg.get("content")
    if not isinstance(content, list):
        return "", []
    text_parts, tool_calls = [], []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text":
            text_parts.append(block.get("text", ""))
        elif btype == "tool_use":
            name = block.get("name", "?")
            inp = block.get("input", {})
            sig_arg = ""
            if isinstance(inp, dict):
                for k in SIG_KEYS:
                    if k in inp:
                        v = str(inp[k])
                        if len(v) > 80:
                            v = v[:77] + "..."
                        sig_arg = f"{k}={v!r}"
                        break
            tool_calls.append(f"{name}({sig_arg})")
    return "\n\n".join(text_parts), tool_calls


def main():
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
    else:
        try:
            transcript_path = json.load(sys.stdin).get("transcript_path")
        except Exception:
            print("error: no transcript path provided", file=sys.stderr)
            sys.exit(1)
        if not transcript_path:
            print("error: transcript_path missing from stdin JSON", file=sys.stderr)
            sys.exit(1)

    transcript_path = Path(transcript_path)
    if not transcript_path.exists():
        print(f"error: transcript not found: {transcript_path}", file=sys.stderr)
        sys.exit(1)

    by_date = defaultdict(list)  # date -> [(ts_local, role, rendered)]
    with transcript_path.open() as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            mtype = d.get("type")
            if mtype not in ("user", "assistant") or not d.get("timestamp"):
                continue
            try:
                ts_local = parse_timestamp(d["timestamp"])
            except ValueError:
                continue
            msg = d.get("message", {})
            if not isinstance(msg, dict):
                continue
            if mtype == "user":
                rendered = render_user(msg).strip()
            else:
                text, tool_calls = render_assistant(msg)
                parts = [text.strip()] if text.strip() else []
                if tool_calls:
                    parts.append("\n".join(f"-> {tc}" for tc in tool_calls))
                rendered = "\n\n".join(parts)
            if rendered:
                by_date[ts_local.strftime("%Y-%m-%d")].append((ts_local, mtype, rendered))

    CONVO_DIR.mkdir(parents=True, exist_ok=True)
    for date, entries in by_date.items():
        lines = [f"# Conversation Log: {date}", ""]
        last = None
        for ts, role, content in entries:
            if (role, content) == last:
                continue  # identical consecutive entries from rapid re-runs
            last = (role, content)
            lines += [f"## [{ts.strftime('%H:%M:%S %Z')}] {role}", "", content, ""]
        out = CONVO_DIR / f"{date}.md"
        tmp = out.with_name(f".{out.name}.{os.getpid()}.tmp")
        tmp.write_text("\n".join(lines))
        os.replace(tmp, out)

    today = datetime.now(LOCAL_TZ).date()
    for f in CONVO_DIR.glob("20*-*-*.md"):
        try:
            if (today - datetime.strptime(f.stem, "%Y-%m-%d").date()).days > RETENTION_DAYS:
                f.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
