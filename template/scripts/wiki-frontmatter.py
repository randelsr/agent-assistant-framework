#!/usr/bin/env python3
"""Add YAML frontmatter to wiki pages that lack it (for Obsidian Dataview queries).

Convention (see CLAUDE.md, "Wiki frontmatter convention"):
  type:    inferred from the page's top-level wiki/ directory
  tags:    [] (fill in by hand)
  created: the file's first git commit date, else its mtime (ISO date)
  updated: the file's last git commit date, else its mtime
  status:  added as "active" only for lifecycle types (project, initiative,
           organization) so Dataview status queries work from day one

Idempotent: pages that already start with frontmatter are never touched.
Default is a dry run that prints what it would add; pass --apply to write.

Config (config/workspace.json, optional) overrides the directory -> type map:
  "wiki": {"type_by_dir": {"people": "person", "vendors": "organization"}}

Usage:
  wiki-frontmatter.py [--apply] [PATH ...]   PATH defaults to all of wiki/
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

WORKSPACE = wc.ROOT
WIKI = WORKSPACE / "wiki"
TYPE_BY_DIR = {
    "people": "person",
    "stakeholders": "stakeholder",
    "organizations": "organization",
    "projects": "project",
    "initiatives": "initiative",
    "concepts": "concept",
    "archive": "archive",
    "topics": "topic",
    "writings": "writing",
}
TYPE_BY_DIR.update(wc.get("wiki.type_by_dir") or {})
LIFECYCLE_TYPES = {"project", "initiative", "organization"}
SPECIAL = {"index.md": "index", "log.md": "log"}


def git_date(path, first):
    args = ["git", "-C", str(WORKSPACE), "log", "--format=%as", "--follow", "--", str(path)]
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=20).stdout.split()
    except Exception:
        return None
    if not out:
        return None
    return out[-1] if first else out[0]


def infer_type(path):
    relp = path.relative_to(WIKI)
    if len(relp.parts) == 1:
        return SPECIAL.get(relp.name, "page")
    return TYPE_BY_DIR.get(relp.parts[0], relp.parts[0].rstrip("s") or "page")


def has_frontmatter(text):
    return text.lstrip("﻿").startswith(("---\n", "---\r\n"))


def build(path):
    t = infer_type(path)
    mtime = datetime.fromtimestamp(path.stat().st_mtime, wc.tz()).date().isoformat()
    created = git_date(path, first=True) or mtime
    updated = git_date(path, first=False) or mtime
    lines = ["---", f"type: {t}"]
    if t in LIFECYCLE_TYPES:
        lines.append("status: active")
    lines += ["tags: []", f"created: {created}", f"updated: {updated}", "---"]
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    targets = [Path(a).resolve() for a in args if not a.startswith("--")] or [WIKI]
    pages = []
    for t in targets:
        pages += [t] if t.is_file() else sorted(t.rglob("*.md"))
    added = skipped = 0
    for p in pages:
        if not str(p).startswith(str(WIKI.resolve()) + os.sep) or p.name == "README.md":
            continue
        text = p.read_text()
        if has_frontmatter(text):
            skipped += 1
            continue
        block = build(p)
        added += 1
        print(f"{'added' if apply else 'would add'}: {p.relative_to(WORKSPACE)}  (type {infer_type(p)})")
        if apply:
            p.write_text(block + "\n\n" + text)
    print(f"\nsummary: {'added' if apply else 'would add'}={added} already-had={skipped}"
          + ("" if apply else "  (dry run; pass --apply to write)"))


if __name__ == "__main__":
    main()
