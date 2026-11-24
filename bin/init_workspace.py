#!/usr/bin/env python3
"""Instantiate an agent workspace from template/ + chosen modules.

    python3 bin/init_workspace.py --config config.toml --dest PATH [--force] [--dry-run]

What it does:
  1. Reads and validates the TOML config (see config.example.toml).
  2. Stages a copy of template/ plus every enabled module:
       modules/<slug>/subagent/  -> subagents/<slug>/
       modules/<slug>/agent.md   -> .claude/agents/<slug>.md
  3. Substitutes {{PLACEHOLDER}} tokens in every text file (and in file names).
     The placeholder name is the upper-case config key, e.g. [agent] name ->
     {{AGENT_NAME}}, [principal] email -> {{PRINCIPAL_EMAIL}}.
  4. Writes config/workspace.json, which the workspace's scripts read at runtime.
  5. Fails loudly, writing nothing, if any {{...}} token is left unfilled.
  6. Copies the staged tree to --dest, runs `git init` there (no commit) and
     prints next steps.

Refuses to write into a non-empty --dest unless --force is given (then files
are overwritten in place; nothing else in dest is deleted).

Python 3.11+, standard library only.
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
        sys.exit("init_workspace.py needs Python 3.11+, or `pip3 install --user tomli` on 3.9/3.10. Found "
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
    "link_check": {"extra_brands": {}, "extra_risky_suffixes": []},
    "wiki": {"type_by_dir": {}},
    "wiki_lint": {"exclude": [], "orphan_exclude": [], "intentional_broken": ["memory/heartbeat-state.json", "memory/inbox-filter/allowlist.json",
                                                         # created at runtime by optional modules
                                                         "wiki/health", "wiki/health/screenings.md", "wiki/fitness",
                                                         "wiki/topics", "wiki/concepts/investment-thesis.md",
                                                         "subagents/finance-analyst/data-snapshot.json",
                                                         "memory/text-thread.md"], "short_basenames": []},
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
    # Framework docs ride along so workspace files can link to docs/*.md.
    if (FRAMEWORK / "docs").is_dir():
        shutil.copytree(FRAMEWORK / "docs", stage / "docs", ignore=IGNORE, dirs_exist_ok=True)
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
    return stats, leftovers


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
     see docs/scripts.md in the framework repo. Each stays off until configured.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Instantiate an agent workspace from the framework template.")
    ap.add_argument("--config", required=True, help="filled-in TOML config (see config.example.toml)")
    ap.add_argument("--dest", required=True, help="directory to create the workspace in")
    ap.add_argument("--force", action="store_true", help="write into a non-empty dest, overwriting files")
    ap.add_argument("--dry-run", action="store_true", help="validate and stage everything, write nothing")
    a = ap.parse_args(argv)

    try:
        placeholders, workspace, modules = validate(load_config(a.config))
    except ConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    dest = Path(os.path.expanduser(a.dest)).resolve()
    if dest_nonempty(dest) and not a.force:
        print(f"ERROR: {dest} exists and is not empty. Use --force to write into it.", file=sys.stderr)
        return 2
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
        cfg_path = stage / "config" / "workspace.json"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(workspace, indent=2, ensure_ascii=False) + "\n")

        if leftovers:
            print(f"ERROR: {len(leftovers)} unfilled placeholder(s); nothing was written:", file=sys.stderr)
            for item in leftovers:
                print(f"  {item}", file=sys.stderr)
            print("Known placeholders: " + ", ".join(sorted("{{%s}}" % k for k in placeholders)), file=sys.stderr)
            return 1

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
