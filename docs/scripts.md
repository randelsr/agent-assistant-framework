# Scripts

Every script in a workspace lives in `scripts/` and reads its settings at runtime from `config/workspace.json`. Nothing personal is baked into code. `bin/init_workspace.py` writes that file from your `config.toml`. To change a value later, edit `config.toml` and re-run init with `--force`, or edit `config/workspace.json` by hand. The model can't edit it: `.claude/settings.json` denies Edit and Write on it.

The scripts need only the macOS system `python3` (3.9+) and the standard library. `bin/init_workspace.py` needs Python 3.11+ because it uses `tomllib`.

## How config reaches the scripts

```
config.toml  --(bin/init_workspace.py)-->  config/workspace.json  --(scripts/workspace_config.py)-->  every script
             \--> `{{...}}` placeholders in text files: settings.json, launchd plist, prompts, docs
```

- `scripts/workspace_config.py` is the shared loader. It finds the workspace root as the parent of `scripts/`, so you can move the workspace without editing anything. Set `AGENT_WORKSPACE` to point a script at another workspace, for tests.
- Hooks never crash a session. If config is missing, they fall back to safe defaults.
- The optional pieces (inbox filter, scoped send, messaging bridge) refuse to run until their config keys are set. They are off by default.
- `{{...}}` placeholders appear only in non-script text: `.claude/settings.json`, `launchd/agent-session.plist` and `scripts/agent-messages-prompt.md`. Init substitutes them, and it fails without writing anything if one is left over.

### workspace.json layout

| Key | From `config.toml` | Used by |
|---|---|---|
| `agent.name / short / emoji / tagline` | `[agent]` | hook messages, Keychain slot names, launchd label |
| `principal.name / email / phone / timezone / profile` | `[principal]` | hook messages, conversation log timezone, quiet hours |
| `workspace.path / os_user / launchd_label / claude_path` | `[workspace]` | launchers. `os_user` is the Keychain account |
| `comms.trusted_senders` | `[comms]` | inbox filter (email entries). The messaging channel plugin enforces phone entries |
| `comms.quiet_hours_start / end` | `[comms]` | scoped send, Messages prompt |
| `modules.enabled` | `[modules]` | informational |
| `inbox.*` | optional `[inbox]` | `inbox-filter.py` |
| `send_email.*` | optional `[send_email]` | `scoped-send-email.py` |
| `messages.*` | optional `[messages]` | messaging bridge |
| `session.*` | optional `[session]` | `agent-session.sh` |
| `heartbeat.*`, `conversations.*` | optional | `login-age.py`, `log-conversation.py` |
| `link_check.*`, `wiki.*`, `wiki_lint.*` | optional | `link_check.py`, `wiki-frontmatter.py`, `wiki-lint.py` |

The optional tables pass straight through. Any key you leave out keeps the default shown in `bin/init_workspace.py` (`OPTIONAL_DEFAULTS`).

## Hooks (wired in `.claude/settings.json`)

| Script | Event | What it does |
|---|---|---|
| `session-start.py` | SessionStart | Stamps `lastSessionStart` in `memory/heartbeat-state.json`. Injects the role rules: only `<Agent> Ops` keeps the heartbeat cron and recreates it if missing, and every other session creates none. This works around session-scoped crons dying on restart. |
| `heartbeat-stamp.py` | UserPromptSubmit | On the heartbeat prompt only, stamps `lastHeartbeatFire`. It records `pendingRecovery` after a gap (more than 15 min since the last fire, or more than 30 min since the last completed turn). Writes are atomic with a rolling backup, and corrupt state is kept for forensics. |
| `ops-freshness.py` | UserPromptSubmit | On non-heartbeat prompts, warns Admin when Ops has stopped firing or has stopped completing turns. |
| `ops-turn-ok.py` | Stop | Stamps `lastOpsTurnOk` only when a heartbeat turn finished without an API error. A cron can keep firing while every turn fails, and this stamp is what catches that. |
| `log-conversation.py` | Stop (async) | Writes the session transcript to `memory/conversations/YYYY-MM-DD.md` in the principal's IANA timezone, using zoneinfo so DST is handled. Deletes logs older than `conversations.retention_days` (default 7). Gitignored. |

UserPromptSubmit ignores `matcher`, so each hook filters on the heartbeat prompt text itself. The marker is `HEARTBEAT.md if it exists`, defined once in `workspace_config.py`. Keep the Ops cron prompt identical to `HEARTBEAT_PROMPT` there.

## Heartbeat helpers

| Script | Use |
|---|---|
| `login-age.py` | Prints JSON with the age of the last `/login` and whether a re-login reminder is due. The heartbeat calls it so the principal can re-login before a long-running session expires. You can tune `heartbeat.login_reminder_days` and `login_expiry_days`. |

## Email: deterministic filter, then a model

### `inbox-filter.py`

This script decides what mail any model is allowed to see. No LLM runs in it.

1. It lists recent mail through the `gog` CLI, with read-only Gmail and Calendar scopes, for `inbox.account`.
2. It keeps a message only if the sender is allowlisted AND Gmail's `Authentication-Results` shows `dmarc=pass`. If the sender's domain publishes no DMARC policy, it accepts `dkim=pass` for that domain instead.
3. For dropped mail it reads nothing (no subject, body or snippet) and writes nothing except the message id and the drop reason.
4. Kept mail goes to `memory/inbox-filter/inbox/<date>-<id>.json`, with links already checked by `link_check.py`. The Ops session passes those files to the Read-only `inbox-triage` subagent.

Allowlist sources:
- `comms.trusted_senders` (email entries) in `config/workspace.json`. These are always allowed.
- `memory/inbox-filter/allowlist.json`: `{"approved": [], "blocked": [], "dkim_aliases": {}}`. The `allow ADDR` and `block ADDR` commands edit it, and only on the principal's explicit word. The model can't edit it directly.

When an unknown sender passes DMARC, only its address and a count are queued in `state.json` `pendingAsk`. Ops asks the principal whether to allow it. Forged mail is dropped without asking.

```
python3 scripts/inbox-filter.py senders --days 90   # who mails this box (addresses + counts only)
python3 scripts/inbox-filter.py fetch               # run by the heartbeat
python3 scripts/inbox-filter.py allow someone@example.com
```

Setup: install `gog` (or set `inbox.gog_path`), authorize it read-only for the mailbox, then set `inbox.account`.

### `link_check.py`

A deterministic phishing check that no model is involved in. A link is followed only if it passes at every redirect hop. It fails on:
- non-https links, raw IP hosts, punycode, user@host tricks, and odd ports
- high-abuse TLDs and instant-hosting domains
- brand lookalikes
- executable downloads
- link text that shows one domain while the link goes to another

The fetch is anonymous: no cookies, no credentials, no JavaScript. Pages are reduced to text, and login or payment pages are flagged. Click-tracker links resolve only when they land on the domain the link text showed.

Add the brands your principal is likely to be phished with (employer, bank, payroll, school) under `link_check.extra_brands`:

```json
"link_check": {"extra_brands": {"examplecorp": ["examplecorp.com"]}}
```

Spot check: `python3 scripts/link_check.py URL [ANCHOR_TEXT]`.

### `scoped-send-email.py`

This is the only email the agent may send, and it's off until `send_email.from` and `send_email.to` are set.
- The sender and recipients come only from config. Nothing on the command line can change them.
- The token has exactly one Gmail scope, `gmail.send`, and the script verifies that on every send. It also refuses if the token belongs to another account.
- The refresh token lives in the Keychain (service `send_email.keychain_service`, default `<short>/gmail-send`, account `workspace.os_user`), separate from any read-only token.
- The body must be `memory/send-outbox/YYYY-MM-DD.md`, and the script allows one send per date (ledger in `memory/send-outbox/sent.json`).
- Quiet hours apply. Messages are plain text, with no attachments and no replies.

```
python3 scripts/scoped-send-email.py auth        # once; the mailbox owner approves gmail.send
python3 scripts/scoped-send-email.py check
python3 scripts/scoped-send-email.py send memory/send-outbox/2026-01-05.md --dry-run
```

It uses the OAuth client in `send_email.credentials_path` (default: gog's `credentials.json`).

## Messaging bridge (macOS)

| File | Role |
|---|---|
| `agent-messages.command` | Runs the long-lived Messages session in Terminal.app, with a fixed session id so restarts resume the same conversation. If claude exits, it relaunches after 10 s. |
| `agent-messages-run.exp` | Answers the development-channel warning when the channel plugin is a local fork, then hands the terminal over. |
| `agent-messages-restart.sh` | Clean restart that stops the launcher loop, expect, claude and the channel server in that order, then verifies exactly one instance. |
| `agent-messages-prompt.md` | The session's system prompt, with placeholders filled at init. It covers routing, pass-through to Admin, quiet hours and the logging format. |
| `messages_config.py` | Prints the bridge and launcher settings as shell assignments for `eval`. Prints nothing and exits non-zero if the config is incomplete. |
| `channel-upstream-check.sh` | Optional daily diff of a forked channel plugin against its upstream snapshot. It never edits the fork. |

Config:

```json
"messages": {
  "channel_plugin": "plugin:imessage@claude-plugins-official",
  "dev_channel": false,
  "enabled_plugins": {"imessage@claude-plugins-official": true},
  "server_pattern": "bun run --cwd .*plugins/imessage",
  "upstream_plugin": "imessage"
}
```

Safety rules:
- Grant Full Disk Access to Terminal.app only.
- Install the channel plugin disabled user-wide. Only this session enables it.
- The session is denied Read and Edit on `~/Library/Messages`, with the Bash sandbox on and no unsandboxed escape, so only the plugin's server reads `chat.db`.
- The plugin must drop every sender not on `comms.trusted_senders` in code, before the model sees anything. If the stock plugin doesn't do this strictly enough, run a strict fork with `dev_channel: true` and track upstream with `channel-upstream-check.sh`.

## Auto-restart under launchd

`scripts/agent-session.sh` plus `launchd/agent-session.plist` (label `[workspace] launchd_label`, default `com.example.agent.<short>`):
- launchd relaunches the session whenever it exits, and the SessionStart hook then rebuilds the heartbeat cron.
- The session resumes with `--continue` under a pseudo-tty (`script -q /dev/null`), because launchd has no terminal.
- If the Keychain slot `session.api_key_keychain_service` (default `<short>/anthropic-api`) holds an API key, it is exported, so a restart never waits for an interactive `/login`. With no key stored, claude uses its normal login.

```
cp launchd/agent-session.plist ~/Library/LaunchAgents/<label>.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<label>.plist
```

Exit any manual `claude` session in the workspace first, or two sessions will fight over `--continue`.

## Voice

`transcribe.sh <audio> [small|medium] [out-prefix]` transcribes offline with whisper.cpp (`brew install whisper-cpp`), converting audio with the built-in `afconvert`. It writes `.txt` and timestamped `.vtt` files. Use `medium` whenever names, numbers or decisions matter. Transcripts are lossy and identify no speakers, so re-listen before quoting anything load-bearing.

## Wiki tools

| Script | Use |
|---|---|
| `wiki-lint.py` | Finds broken links (markdown links and backticked paths that include a directory), orphan wiki pages, and pages missing the required frontmatter (`type`, `tags`, `created`, `updated`). Orphan directories are derived from `wiki/`, never listed by hand, so a new directory is checked by default. Opt-outs go in `wiki_lint`. Exits 1 on findings. |
| `wiki-frontmatter.py` | Adds frontmatter to pages that lack it, inferring `type` from the directory (override with `wiki.type_by_dir`) and dates from git history. Defaults to a dry run; pass `--apply` to write. Never touches a page that already has frontmatter. |

## Keychain convention

Service `<short-lowercase>/<purpose>`, account `workspace.os_user`:

```
security add-generic-password -U -s "atl/anthropic-api" -a "$USER" -w
```

Record the slot name in `TOOLS.md`. Never record the value.
