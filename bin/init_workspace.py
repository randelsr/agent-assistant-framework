#!/usr/bin/env python3
"""Instantiate an agent workspace from template/ + chosen modules.

    python3 bin/init_workspace.py --config config.toml --dest PATH [--dry-run]
    python3 bin/init_workspace.py --config config.toml --dest PATH --update-config [--dry-run]
    python3 bin/init_workspace.py --config config.toml --dest PATH --force [--dry-run]

What it does:
  1. Reads and validates the TOML config (see config.example.toml).
  2. Stages a copy of template/ plus every enabled module:
       modules/<slug>/subagent/  -> subagents/<slug>/
       modules/<slug>/agent.md   -> .claude/agents/<slug>.md
  3. Moves each enabled module's dispatch row into the HEARTBEAT.md table and
     adds a row per installed module to the subagents/README.md
     "Installed subagents" table.
  4. Substitutes {{PLACEHOLDER}} tokens in every text file (and in file names).
     The placeholder name is the upper-case config key, e.g. [agent] name ->
     {{AGENT_NAME}}, [principal] email -> {{PRINCIPAL_EMAIL}}.
  5. Writes config/workspace.json, which the workspace's scripts read at runtime.
  6. Fails loudly, writing nothing, if any {{...}} token is left unfilled.
  7. Copies the staged tree to --dest, runs `git init` there (no commit) and
     prints next steps.

Refuses to write into a non-empty --dest unless --update-config or --force is
given.

--update-config (the safe way to change a setting on an existing workspace):
  - regenerates config/workspace.json (previous copy kept as
    config/workspace.json.bak) and keeps the existing messages.session_id
    unless config.toml sets one;
  - regenerates the files that are purely derived from config
    (DERIVED_FILES below) only if they still match what the previous config
    produced; a hand-edited one is left alone and the new version is written
    next to it as <file>.new;
  - installs newly enabled modules (subagents/<slug>/ and
    .claude/agents/<slug>.md), copying only files that do not exist yet, and
    adds their HEARTBEAT.md dispatch rows and subagents/README.md rows;
  - never overwrites anything else (USER.md, IDENTITY.md, MEMORY.md, memory/,
    wiki/ and module files you have edited are untouched) and never deletes.

--force re-runs the full init over an existing directory and OVERWRITES every
template file, including the personalized ones (USER.md, IDENTITY.md, SOUL.md,
MEMORY.md, memory/missions.md, wiki seeds, subagent MEMORY.md files). Nothing
else in dest is deleted. The existing messages.session_id is kept.

Python 3.9+, standard library only (plus `pip3 install --user tomli` on
3.9/3.10, where tomllib is not built in).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # Python 3.9/3.10: pip3 install --user tomli
    except ModuleNotFoundError:
        sys.exit("init_workspace.py needs Python 3.9+ with `pip3 install --user tomli` (built in as tomllib on 3.11+). Found "
                 + sys.version.split()[0] + ".")
import uuid
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

FRAMEWORK = Path(__file__).resolve().parent.parent
TEMPLATE = FRAMEWORK / "template"
MODULES = FRAMEWORK / "modules"
ALWAYS_MODULES = ["librarian", "research"]
IGNORE = shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc")
TOKEN_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24}$")
PHONE_RE = re.compile(r"^\+[1-9]\d{6,14}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
EXECUTABLE_SUFFIXES = {".py", ".sh", ".command", ".exp"}
# Files whose whole content is the template plus config values. --update-config
# regenerates them when they still match the previous config's rendering.
DERIVED_FILES = [".claude/settings.json", "launchd/agent-session.plist", "scripts/agent-messages-prompt.md"]
DISPATCH_BLOCK_RE = re.compile(r"<!-- Optional module rows\..*?-->\n?", re.S)
DISPATCH_ROW_RE = re.compile(r"^module:([a-z0-9-]+) (\|.*\|)[ \t]*$")

# Optional TOML tables passed straight through into workspace.json, merged over
# these defaults. Everything personal defaults to empty, so each optional piece
# is off (fail-closed) until configured.
OPTIONAL_DEFAULTS = {
    "inbox": {"account": "", "gog_path": "", "window_days": 14},
    "send_email": {"from": "", "from_display": "", "to": [], "subject": "{agent} update: {date}",
                   "credentials_path": "", "keychain_service": ""},
    "messages": {"channel_plugin": "", "dev_channel": False, "enabled_plugins": {}, "session_name": "",
                 "session_id": "", "server_pattern": "", "upstream_plugin": "",
                 "deny_read_paths": ["~/Library/Messages/**"], "env": {}},
    "session": {"channels": "", "api_key_keychain_service": ""},
    "heartbeat": {"login_reminder_days": 25, "login_expiry_days": 27.5},
    "conversations": {"retention_days": 7},
    "link_check": {"extra_brands": {}, "extra_risky_suffixes": [], "registrable_domain_patterns": []},
    "wiki": {"type_by_dir": {}},
    "wiki_lint": {"exclude": [], "orphan_exclude": [], "intentional_broken": ["memory/heartbeat-state.json", "memory/inbox-filter/allowlist.json",
                                                         # created at runtime by optional modules
                                                         "wiki/health", "wiki/health/screenings.md", "wiki/fitness",
                                                         "wiki/topics", "wiki/concepts/investment-thesis.md",
                                                         "subagents/finance-analyst/data-snapshot.json",
                                                         "memory/text-thread.md",  # meal-planner message mode
                                                         # created at runtime by the messaging bridge
                                                         "memory/messages-log.md", "memory/messages-acks.md"],
                  "short_basenames": []},
}


class ConfigError(Exception):
    pass


def load_config(path):
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: invalid TOML: {e}")


def validate(cfg):
    """Return (placeholders, workspace_json). Raises ConfigError listing every problem."""
    errs = []

    def need(table, key, kind=str):
        v = (cfg.get(table) or {}).get(key)
        if v is None or (kind is str and not str(v).strip()):
            errs.append(f"[{table}] {key} is required")
            return kind() if kind in (str, list) else None
        if kind is not None and not isinstance(v, kind):
            errs.append(f"[{table}] {key} must be {kind.__name__}")
        return v

    agent = {k: need("agent", k) for k in ("name", "short", "emoji", "tagline")}
    principal = {k: need("principal", k) for k in ("name", "full_name", "email", "phone", "timezone", "profile")}
    ws = {k: need("workspace", k) for k in ("path", "os_user")}
    senders = need("comms", "trusted_senders", list)
    qs = need("comms", "quiet_hours_start", int)
    qe = need("comms", "quiet_hours_end", int)
    enabled = (cfg.get("modules") or {}).get("enabled", [])

    if agent["short"] and not re.fullmatch(r"[A-Za-z0-9]{2,4}", agent["short"]):
        errs.append("[agent] short must be 2-4 letters or digits")
    if principal["email"] and not EMAIL_RE.match(principal["email"]):
        errs.append("[principal] email is not a valid address")
    if principal["phone"] and not PHONE_RE.match(principal["phone"]):
        errs.append("[principal] phone must be E.164, e.g. +15555550100")
    if principal["profile"] and principal["profile"] not in ("work", "personal"):
        errs.append('[principal] profile must be "work" or "personal"')
    if principal["timezone"]:
        try:
            ZoneInfo(principal["timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            errs.append(f"[principal] timezone {principal['timezone']!r} is not an IANA zone name")
    if ws["path"] and not os.path.isabs(os.path.expanduser(ws["path"])):
        errs.append("[workspace] path must be absolute")
    if ws["os_user"] and not re.fullmatch(r"[A-Za-z0-9._-]+", ws["os_user"]):
        errs.append("[workspace] os_user has unexpected characters")
    for s in senders if isinstance(senders, list) else []:
        if not isinstance(s, str) or not (EMAIL_RE.match(s) or PHONE_RE.match(s)):
            errs.append(f"[comms] trusted_senders entry {s!r} is neither an email nor an E.164 number")
    for name, v in (("quiet_hours_start", qs), ("quiet_hours_end", qe)):
        if isinstance(v, int) and not 0 <= v <= 23:
            errs.append(f"[comms] {name} must be 0-23")
    if not isinstance(enabled, list) or not all(isinstance(m, str) and SLUG_RE.match(m) for m in enabled):
        errs.append("[modules] enabled must be a list of module slugs")
        enabled = []
    for table, defaults in OPTIONAL_DEFAULTS.items():
        if table in cfg and not isinstance(cfg[table], dict):
            errs.append(f"[{table}] must be a table")
    if errs:
        raise ConfigError("config problems:\n  - " + "\n  - ".join(errs))

    ws_path = os.path.expanduser(ws["path"])
    modules = list(dict.fromkeys(ALWAYS_MODULES + enabled))
    short_lower = agent["short"].lower()
    placeholders = {
        "AGENT_NAME": agent["name"],
        "AGENT_SHORT": agent["short"],
        "AGENT_SHORT_LOWER": short_lower,
        "AGENT_EMOJI": agent["emoji"],
        "AGENT_TAGLINE": agent["tagline"],
        "PRINCIPAL_NAME": principal["name"],
        "PRINCIPAL_FULL_NAME": principal["full_name"],
        "PRINCIPAL_EMAIL": principal["email"],
        "PRINCIPAL_PHONE": principal["phone"],
        "TIMEZONE": principal["timezone"],
        "PROFILE": principal["profile"],
        "WORKSPACE_PATH": ws_path,
        "OS_USER": ws["os_user"],
        "TRUSTED_SENDERS": json.dumps(senders),
        "QUIET_START": f"{qs:02d}",
        "QUIET_END": f"{qe:02d}",
        "LAUNCHD_LABEL": (cfg.get("workspace") or {}).get("launchd_label") or f"com.example.agent.{short_lower}",
        "MODULES_ENABLED": json.dumps(modules),
        "TODAY": date.today().isoformat(),
        "YEAR": str(date.today().year),
    }

    workspace = {
        "_comment": "Written by bin/init_workspace.py. Scripts read this at runtime. "
                    "Holds no secrets; secrets live in the macOS Keychain.",
        "agent": agent,
        "principal": principal,
        "workspace": {"path": ws_path, "os_user": ws["os_user"],
                      "launchd_label": placeholders["LAUNCHD_LABEL"],
                      "claude_path": (cfg.get("workspace") or {}).get("claude_path", "")},
        "comms": {"trusted_senders": senders, "quiet_hours_start": qs, "quiet_hours_end": qe},
        "modules": {"enabled": modules},
    }
    for table, defaults in OPTIONAL_DEFAULTS.items():
        merged = json.loads(json.dumps(defaults))
        merged.update(cfg.get(table) or {})
        workspace[table] = merged
    if not workspace["messages"]["session_id"]:
        workspace["messages"]["session_id"] = str(uuid.uuid4())
    if not workspace["messages"]["session_name"]:
        workspace["messages"]["session_name"] = f"{agent['name']} Messages"
    return placeholders, workspace, modules


def is_text(data):
    if b"\0" in data[:8192]:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def substitute(text, placeholders):
    return TOKEN_RE.sub(lambda m: placeholders.get(m.group(0)[2:-2], m.group(0)), text)


def stage_tree(stage, modules, placeholders):
    """Copy template + modules into stage, substitute. Returns (stats, leftovers)."""
    if not TEMPLATE.is_dir():
        raise ConfigError(f"template directory missing: {TEMPLATE}")
    shutil.copytree(TEMPLATE, stage, ignore=IGNORE, dirs_exist_ok=True)
    missing = []
    for slug in modules:
        if (TEMPLATE / "subagents" / slug).is_dir():
            continue  # core subagent, already shipped inside template/
        mdir = MODULES / slug
        sub, agent_md = mdir / "subagent", mdir / "agent.md"
        if not sub.is_dir() or not agent_md.is_file():
            missing.append(slug)
            continue
        shutil.copytree(sub, stage / "subagents" / slug, ignore=IGNORE, dirs_exist_ok=True)
        (stage / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
        shutil.copy2(agent_md, stage / ".claude" / "agents" / f"{slug}.md")
    if missing:
        raise ConfigError("module(s) not found or incomplete (need subagent/ and agent.md): "
                          + ", ".join(f"modules/{m}" for m in missing))

    stats = {"files": 0, "text": 0, "substituted": 0}
    leftovers = []
    # Deepest paths first so renaming a directory never invalidates a pending child.
    for path in sorted(stage.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_file() and not path.is_symlink():
            stats["files"] += 1
            data = path.read_bytes()
            if is_text(data):
                stats["text"] += 1
                text = data.decode("utf-8")
                new = substitute(text, placeholders)
                if new != text:
                    stats["substituted"] += 1
                    path.write_text(new, encoding="utf-8")
                for tok in sorted(set(TOKEN_RE.findall(new))):
                    leftovers.append(f"{path.relative_to(stage)}: {tok}")
        new_name = substitute(path.name, placeholders)
        if new_name != path.name:
            path.rename(path.with_name(new_name))
        for tok in TOKEN_RE.findall(new_name):
            leftovers.append(f"{path.relative_to(stage)} (file name): {tok}")
    # Framework docs ride along verbatim (after substitution, so their literal
    # {{PLACEHOLDER}} examples survive) and workspace files can link to docs/*.md.
    if (FRAMEWORK / "docs").is_dir():
        shutil.copytree(FRAMEWORK / "docs", stage / "docs", ignore=IGNORE, dirs_exist_ok=True)
    return stats, leftovers


def install_dispatch_rows(text, modules):
    """Move the HEARTBEAT.md optional-row line of each enabled module from the
    commented block into the dispatch table right above it. Returns (text, added)."""
    m = DISPATCH_BLOCK_RE.search(text)
    if not m:
        return text, []
    keep, rows, added = [], [], []
    for line in m.group(0).split("\n"):
        r = DISPATCH_ROW_RE.match(line)
        if r and r.group(1) in modules:
            if r.group(2) not in text[:m.start()]:
                rows.append(r.group(2))
                added.append(r.group(1))
            continue
        keep.append(line)
    if not added and len(keep) == len(m.group(0).split("\n")):
        return text, []
    before = text[:m.start()].split("\n")
    # Insert after the last table row that precedes the block.
    idx = max((i for i, ln in enumerate(before) if ln.startswith("|")), default=None)
    if idx is None:
        return text, []
    before[idx + 1:idx + 1] = rows
    return "\n".join(before) + "\n".join(keep) + text[m.end():], added


def module_row(slug, readme_text):
    """Row for the 'Installed subagents' table, built from the Modules table and MODULE.md."""
    domain = "see `subagents/%s/SCOPE.md`" % slug
    for line in readme_text.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == "`%s`" % slug:
            domain = cells[1]
            break
    thread = "No"
    mod = MODULES / slug / "MODULE.md"
    if mod.is_file():
        tm = re.search(r"\*\*Thread mode:\*\*\s*(\w+)", mod.read_text(encoding="utf-8"))
        if tm and tm.group(1).lower() == "yes":
            thread = "Supported"
    return "| `%s` | %s | %s | Active |" % (slug, domain, thread)


def install_subagent_rows(text, modules):
    """Add a row per installed module to the 'Installed subagents' table. Returns (text, added)."""
    lines = text.split("\n")
    try:
        h = next(i for i, ln in enumerate(lines) if ln.strip() == "## Installed subagents")
    except StopIteration:
        return text, []
    i = h + 1
    while i < len(lines) and not lines[i].startswith("|"):
        i += 1
    if i >= len(lines):
        return text, []
    j = i
    present = set()
    while j < len(lines) and lines[j].startswith("|"):
        first = lines[j].strip().strip("|").split("|")[0].strip()
        if first.startswith("`") and first.endswith("`"):
            present.add(first.strip("`"))
        j += 1
    added = [s for s in modules if s not in present]
    lines[j:j] = [module_row(s, text) for s in added]
    return "\n".join(lines), added


def apply_registries(root, modules, dry_run=False):
    """Run both registry updates on files under root. Returns {relpath: [slugs added]}."""
    out = {}
    for rel, fn in (("HEARTBEAT.md", install_dispatch_rows), ("subagents/README.md", install_subagent_rows)):
        f = root / rel
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        new, added = fn(text, modules)
        if new != text:
            out[rel] = added
            if not dry_run:
                f.write_text(new, encoding="utf-8")
    return out


def read_workspace_json(dest):
    try:
        return json.loads((dest / "config" / "workspace.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def dest_nonempty(dest):
    return dest.exists() and any(dest.iterdir())


def make_executable(root):
    for p in (root / "scripts").rglob("*") if (root / "scripts").is_dir() else []:
        if p.is_file() and (p.suffix in EXECUTABLE_SUFFIXES):
            p.chmod(p.stat().st_mode | 0o111)


def git_init(dest):
    if (dest / ".git").exists():
        return "existing git repo left as is"
    r = subprocess.run(["git", "init", "-q", "-b", "main", str(dest)], capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(["git", "init", "-q", str(dest)], capture_output=True, text=True)
    return "git init done (no commit)" if r.returncode == 0 else f"git init FAILED: {r.stderr.strip()}"


def source_files(modules):
    """Yield (workspace-relative path, framework source path) for template and module text files."""
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_file():
            yield str(src.relative_to(TEMPLATE)), src
    for slug in modules:
        if (TEMPLATE / "subagents" / slug).is_dir():
            continue
        sub = MODULES / slug / "subagent"
        for src in sorted(sub.rglob("*")) if sub.is_dir() else []:
            if src.is_file():
                yield "subagents/%s/%s" % (slug, src.relative_to(sub)), src
        if (MODULES / slug / "agent.md").is_file():
            yield ".claude/agents/%s.md" % slug, MODULES / slug / "agent.md"



def update_config(stage, dest, placeholders, workspace, modules, prev, dry_run):
    """Apply --update-config from a fully staged tree. Never overwrites a personalized file."""
    def did(past):  # "regenerated" or, on a dry run, "would be regenerated"
        return ("would be " + past) if dry_run else past
    actions, warnings = [], []

    def write(path, text):
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    # 1. config/workspace.json
    ws_path = dest / "config" / "workspace.json"
    new_ws = json.dumps(workspace, indent=2, ensure_ascii=False) + "\n"
    old_ws = ws_path.read_text(encoding="utf-8")
    if new_ws == old_ws:
        actions.append("config/workspace.json: unchanged")
    else:
        changed = sorted(k for k in set(workspace) | set(prev) if workspace.get(k) != prev.get(k))
        if not dry_run:
            shutil.copy2(ws_path, ws_path.with_name("workspace.json.bak"))
        write(ws_path, new_ws)
        actions.append("config/workspace.json: %s (changed: %s; previous copy -> config/workspace.json.bak)"
                       % ("would be rewritten" if dry_run else "rewritten", ", ".join(changed) or "formatting"))

    # 2. Files derived purely from config.
    try:
        old_placeholders = validate(prev)[0]
    except ConfigError:
        old_placeholders = None
    for rel in DERIVED_FILES:
        src_template, staged, target = TEMPLATE / rel, stage / rel, dest / rel
        if not staged.is_file():
            continue
        new_text = staged.read_text(encoding="utf-8")
        if not target.is_file():
            write(target, new_text)
            actions.append(f"{rel}: missing, {did('created')}")
            continue
        cur = target.read_text(encoding="utf-8")
        if cur == new_text:
            continue
        old_render = (substitute(src_template.read_text(encoding="utf-8"), old_placeholders)
                      if old_placeholders and src_template.is_file() else None)
        if cur == old_render:
            write(target, new_text)
            actions.append(f"{rel}: {did('regenerated')} from the new config")
        else:
            write(target.with_name(target.name + ".new"), new_text)
            warnings.append(f"{rel} has local edits, left as is; new version {did('written')} to {rel}.new. "
                            f"Merge by hand, then delete the .new file.")

    # 2b. Personalizable files that embed a changed value are never rewritten; list them.
    prev_modules = set((prev.get("modules") or {}).get("enabled") or [])
    if old_placeholders:
        changed_keys = sorted(k for k, v in placeholders.items()
                              if k not in ("TODAY", "YEAR") and old_placeholders.get(k) != v)
        if changed_keys:
            tokens = ["{{%s}}" % k for k in changed_keys]
            hits, seen = [], set()
            for rel, src in source_files(sorted(prev_modules)):
                if rel in DERIVED_FILES:
                    continue
                try:
                    text = src.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                found = [k for k, tok in zip(changed_keys, tokens) if tok in text]
                if found and (dest / rel).is_file():
                    hits.append(rel)
                    seen.update(found)
            if hits:
                warnings.append("these files embed values that changed (%s) and were left as is so your edits "
                                "survive; update them by hand if they matter: %s"
                                % (", ".join(k for k in changed_keys if k in seen), ", ".join(hits)))

    # 3. Newly enabled modules: copy only files that do not exist yet.
    for slug in modules:
        files = []
        sub = stage / "subagents" / slug
        if sub.is_dir():
            files += [p for p in sorted(sub.rglob("*")) if p.is_file()]
        agent_md = stage / ".claude" / "agents" / f"{slug}.md"
        if agent_md.is_file():
            files.append(agent_md)
        new_files = [p for p in files if not (dest / p.relative_to(stage)).exists()]
        if not new_files:
            continue
        if slug in prev_modules and (dest / "subagents" / slug).is_dir():
            continue  # installed before; a missing file was probably removed on purpose
        for p in new_files:
            target = dest / p.relative_to(stage)
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
        actions.append(f"module {slug}: {len(new_files)} new file(s) {did('installed')}")
    for slug in sorted(prev_modules - set(modules)):
        warnings.append(f"module {slug} is installed but no longer enabled. Nothing was removed; "
                        f"delete subagents/{slug}/ and .claude/agents/{slug}.md by hand if you want it gone.")

    # 4. Registries (targeted line inserts, never a rewrite of the rest of the file).
    for rel, added in apply_registries(dest, modules, dry_run).items():
        actions.append(f"{rel}: rows {did('added')} for {', '.join(dict.fromkeys(added))}")
    if not dry_run:
        make_executable(dest)
    return actions, warnings


def next_steps(dest, placeholders):
    name = placeholders["AGENT_NAME"]
    return f"""
Next steps:
  1. cd {dest}
     Review config/workspace.json. It holds no secrets; keep the repo private anyway.
  2. Create a PRIVATE remote and push. Commit when you're ready (nothing is committed yet).
  3. Open Claude Code here and say: "Bootstrap. Walk me through filling in IDENTITY, SOUL,
     USER and wiki/people/principal.md."
  4. Start a second session for Ops with the prompt "You are {name} Ops." The SessionStart
     hook tells it to create the heartbeat cron.
  5. Optional pieces (inbox filter, scoped send, messaging bridge, launchd, transcription):
     see docs/scripts.md in this workspace (a copy of the framework docs ships in docs/).
     Each stays off until configured.
  6. To change a setting later, edit config.toml and run
     bin/init_workspace.py --config config.toml --dest {dest} --update-config
     from the framework repo. Do NOT use --force on a workspace you have personalized.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Instantiate an agent workspace from the framework template.")
    ap.add_argument("--config", required=True, help="filled-in TOML config (see config.example.toml)")
    ap.add_argument("--dest", required=True, help="directory to create the workspace in")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--update-config", action="store_true",
                      help="existing workspace: regenerate config/workspace.json and config-derived files, "
                           "install newly enabled modules; never overwrites personalized files")
    mode.add_argument("--force", action="store_true",
                      help="write into a non-empty dest, OVERWRITING every template file, including "
                           "USER.md, IDENTITY.md, MEMORY.md, missions and wiki seeds")
    ap.add_argument("--dry-run", action="store_true", help="validate and stage everything, write nothing")
    a = ap.parse_args(argv)

    try:
        cfg = load_config(a.config)
        placeholders, workspace, modules = validate(cfg)
    except ConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    dest = Path(os.path.expanduser(a.dest)).resolve()
    prev = read_workspace_json(dest) if dest.is_dir() else None
    if a.update_config and prev is None:
        print(f"ERROR: {dest}/config/workspace.json is missing or unreadable; --update-config needs an "
              f"initialized workspace. Run without it to create one.", file=sys.stderr)
        return 2
    if dest_nonempty(dest) and not (a.force or a.update_config):
        print(f"ERROR: {dest} exists and is not empty. To change settings on an existing workspace use "
              f"--update-config. (--force overwrites personalized files.)", file=sys.stderr)
        return 2
    if a.force and dest_nonempty(dest):
        print(f"WARNING: --force overwrites every template file in {dest}, including USER.md, IDENTITY.md,\n"
              f"         SOUL.md, MEMORY.md, memory/missions.md, wiki seeds and subagent MEMORY.md files.\n"
              f"         To change settings without losing personalization, use --update-config instead.",
              file=sys.stderr)
    # Keep the Messages session id stable across re-runs unless config.toml pins one.
    if prev and not ((cfg.get("messages") or {}).get("session_id")):
        prev_id = (prev.get("messages") or {}).get("session_id")
        if prev_id:
            workspace["messages"]["session_id"] = prev_id
    if Path(placeholders["WORKSPACE_PATH"]).resolve() != dest:
        print(f"WARNING: [workspace] path is {placeholders['WORKSPACE_PATH']} but --dest is {dest}.\n"
              f"         Hooks, plists and scripts will point at the config path. Move the workspace there,\n"
              f"         or fix the config and re-run.", file=sys.stderr)

    stage = Path(tempfile.mkdtemp(prefix="init-workspace-"))
    try:
        try:
            stats, leftovers = stage_tree(stage, modules, placeholders)
        except ConfigError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        apply_registries(stage, modules)
        cfg_path = stage / "config" / "workspace.json"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(workspace, indent=2, ensure_ascii=False) + "\n")

        if leftovers:
            print(f"ERROR: {len(leftovers)} unfilled placeholder(s); nothing was written:", file=sys.stderr)
            for item in leftovers:
                print(f"  {item}", file=sys.stderr)
            print("Known placeholders: " + ", ".join(sorted("{{%s}}" % k for k in placeholders)), file=sys.stderr)
            return 1

        if a.update_config:
            print(f"{'DRY RUN: would update' if a.dry_run else 'Updating'} config of workspace at {dest}")
            print(f"  modules: {', '.join(modules)}")
            actions, warnings = update_config(stage, dest, placeholders, workspace, modules, prev, a.dry_run)
            for line in actions:
                print(f"  {line}")
            for line in warnings:
                print(f"WARNING: {line}", file=sys.stderr)
            print("  personalized files (USER.md, IDENTITY.md, MEMORY.md, memory/, wiki/, edited module files): untouched")
            if a.dry_run:
                print("\nNothing written. Re-run without --dry-run to apply.")
            return 0

        print(f"{'DRY RUN: would create' if a.dry_run else 'Creating'} workspace at {dest}")
        print(f"  modules: {', '.join(modules)}")
        print(f"  files: {stats['files']} ({stats['text']} text, {stats['substituted']} with substitutions)")
        print("  config/workspace.json: written" if not a.dry_run else "  config/workspace.json: would be written")
        if a.dry_run:
            print("\nNothing written. Re-run without --dry-run to create it.")
            return 0

        dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stage, dest, symlinks=True, dirs_exist_ok=True)
        make_executable(dest)
        print(f"  {git_init(dest)}")
        print(next_steps(dest, placeholders))
        return 0
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
