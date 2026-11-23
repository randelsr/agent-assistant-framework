#!/usr/bin/env python3
"""Wiki link + orphan + frontmatter audit.

Scans the workspace's curated content (root *.md scaffolding + wiki/ +
memory/missions.md + memory/active-work.md + subagents/) for:
  1. Broken links: a markdown link or backticked path whose target doesn't exist
  2. Orphan pages: wiki/ pages with no inbound link from any scanned source
  3. Frontmatter gaps: wiki/ pages missing frontmatter or a required field
     (type, tags, created, updated)

Skips raw/, memory/conversations/ and wiki/log.md as link sources (historical or
immutable). Exit 1 if anything is found, 0 if clean.

Orphan directories are DERIVED (every subdirectory of wiki/), never enumerated.
An enumerated list silently falls behind when someone adds a directory, and the
failure is invisible: pages in the new directory are never checked and the
linter reports clean. Opt OUT explicitly via config; never opt in.

Config (config/workspace.json, all optional):
  "wiki_lint": {
    "exclude": ["wiki/archive/imported"],      source paths not scanned for links
    "orphan_exclude": ["wiki/archive/imported"],
    "intentional_broken": ["wiki/old-page.md"], targets allowed to be missing
    "short_basenames": ["notes.md"]             prose basenames not resolved
  }

Usage: wiki-lint.py [--no-frontmatter]
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace_config as wc  # noqa: E402

WORKSPACE = wc.ROOT
WIKI = WORKSPACE / "wiki"


def _paths(key, default=()):
    return {WORKSPACE / p for p in (wc.get(f"wiki_lint.{key}") or list(default))}


SCAN_ROOTS = sorted(WORKSPACE.glob("*.md")) + [
    WIKI,
    WORKSPACE / "subagents",
    WORKSPACE / "memory" / "missions.md",
    WORKSPACE / "memory" / "active-work.md",
]
EXCLUDE = {WIKI / "log.md", WORKSPACE / "raw", WORKSPACE / "memory" / "conversations"} | _paths("exclude")
ORPHAN_EXCLUDE = _paths("orphan_exclude")
INTENTIONAL_BROKEN = set(wc.get("wiki_lint.intentional_broken") or [])
# Short basenames used as nouns in prose and cheat-sheet tables; don't resolve.
SHORT_BASENAME_TARGETS = {
    "missions.md", "active-work.md", "heartbeat-state.json", "index.md", "log.md", "SKILL.md",
    "SCOPE.md", "RULES.md", "MEMORY.md", "IDENTITY.md", "SOUL.md", "USER.md", "TOOLS.md",
    "HEARTBEAT.md", "CLAUDE.md", "README.md", "outbox.md", "workspace.json",
} | set(wc.get("wiki_lint.short_basenames") or [])
REQUIRED_FIELDS = ("type", "tags", "created", "updated")
NO_FRONTMATTER = {WIKI / "index.md", WIKI / "log.md"}

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(r"`([^`]*?\.(?:md|py|sh|css|json|html|jsonl|srt|m4a|pdf|png|jpg|xlsx|docx|txt))`")
BARE_BACKTICK_DIR_RE = re.compile(r"`((?:wiki|memory|raw|scripts|subagents)/[^`\s]+/?)`")
PATTERN_INDICATORS = ("<", ">", "*", "YYYY", "{", "}", "?", "$")


def excluded(p):
    return any(p == e or str(p).startswith(str(e) + os.sep) for e in EXCLUDE)


def collect_md_files(roots):
    files = []
    for root in roots:
        if root.is_file() and root.suffix == ".md" and not excluded(root):
            files.append(root)
        elif root.is_dir():
            files += [p for p in root.rglob("*.md") if not excluded(p)]
    return sorted(set(files))


def resolve_link(source, target, kind):
    """Return candidate paths (any one existing = valid); [] means don't check."""
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:", "file://", ".")):
        return []
    if any(p in target for p in PATTERN_INDICATORS):
        return []
    if target.rstrip("/") in INTENTIONAL_BROKEN or target in INTENTIONAL_BROKEN:
        return []
    if target in SHORT_BASENAME_TARGETS:
        return []
    # A backticked bare file name ("notes.md") is a noun in prose or an example,
    # not a reference. Only backticked paths with a directory are checked.
    if kind == "backtick" and "/" not in target:
        return []
    if target.startswith("/"):
        return [Path(target)]
    candidates = [(source.parent / target).resolve()]
    if kind == "backtick":
        candidates.append((WORKSPACE / target).resolve())
    return candidates


def extract_references(file):
    try:
        text = file.read_text()
    except Exception:
        return
    # Fenced code blocks are examples, not references.
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for m in LINK_RE.finditer(text):
        yield "link", m.group(2)
    for m in BACKTICK_PATH_RE.finditer(text):
        yield "backtick", m.group(1)
    for m in BARE_BACKTICK_DIR_RE.finditer(text):
        yield "backtick", m.group(1)


def frontmatter_fields(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    return {ln.split(":", 1)[0].strip() for ln in text[4:end].splitlines() if ":" in ln and not ln.startswith(" ")}


def rel(p):
    try:
        return p.relative_to(WORKSPACE)
    except ValueError:
        return p


def main():
    check_fm = "--no-frontmatter" not in sys.argv[1:]
    files = collect_md_files(SCAN_ROOTS)
    print(f"scanning {len(files)} files\n")

    broken, inbound = [], defaultdict(set)
    for f in files:
        for kind, target in extract_references(f):
            candidates = resolve_link(f, target, kind)
            if not candidates:
                continue
            existing = [c for c in candidates if c.exists()]
            if not existing:
                broken.append((f, kind, target))
            for c in existing:
                if str(c).startswith(str(WIKI) + os.sep):
                    inbound[c].add(f)

    orphans, fm_gaps = [], []
    if WIKI.exists():
        for d in sorted(x for x in WIKI.iterdir() if x.is_dir() and not x.name.startswith(".")):
            for page in sorted(d.rglob("*.md")):
                if page.name == "README.md" or any(str(page).startswith(str(e)) for e in ORPHAN_EXCLUDE):
                    continue
                if page not in inbound:
                    orphans.append(page)
        if check_fm:
            for page in sorted(WIKI.rglob("*.md")):
                if page in NO_FRONTMATTER or page.name == "README.md" or excluded(page):
                    continue
                fields = frontmatter_fields(page.read_text())
                if fields is None:
                    fm_gaps.append((page, "no frontmatter"))
                else:
                    missing = [k for k in REQUIRED_FIELDS if k not in fields]
                    if missing:
                        fm_gaps.append((page, "missing " + ", ".join(missing)))

    bar = "=" * 70
    print(f"{bar}\nBROKEN LINKS ({len(broken)})\n{bar}")
    for source, kind, target in broken:
        print(f"  {rel(source)} -> [{kind}] {target}")
    if not broken:
        print("  none")
    print(f"\n{bar}\nORPHAN WIKI PAGES ({len(orphans)}): pages with no inbound link\n{bar}")
    for o in orphans:
        print(f"  {rel(o)}")
    if not orphans:
        print("  none")
    if check_fm:
        print(f"\n{bar}\nFRONTMATTER GAPS ({len(fm_gaps)})\n{bar}")
        for page, why in fm_gaps:
            print(f"  {rel(page)}: {why}")
        if not fm_gaps:
            print("  none")
    print()
    sys.exit(1 if (broken or orphans or fm_gaps) else 0)


if __name__ == "__main__":
    main()
