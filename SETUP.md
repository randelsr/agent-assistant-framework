# Setup

About an hour for the core and another hour per optional piece. Run every command from your instantiated workspace unless a step says otherwise.

## 1. Instantiate

```bash
cp config.example.toml config.toml
```

Fill in `config.toml`:
- **`[agent]`**: your agent's name, short handle and emoji. The short handle shows up in tags and filenames.
- **`[principal]`**: who the agent works for. `profile` is `work` or `personal`.
- **`[workspace] path`**: the absolute path where the workspace will live.
- **`[comms] trusted_senders`**: the only addresses and numbers whose messages ever reach a model. Keep it short.
- **`[modules] enabled`**: which optional subagents to install.

```bash
python3 bin/init_workspace.py --config config.toml --dest /absolute/path/from/config --dry-run
python3 bin/init_workspace.py --config config.toml --dest /absolute/path/from/config
```

The init script refuses to finish if any `{{PLACEHOLDER}}` is left unfilled.

Put the new workspace in a **private** git repo. It will hold personal data from day one.

## 2. Make it yours (first session)

Open the workspace in Claude Code and say: "Bootstrap. Walk me through filling in IDENTITY, SOUL, USER and wiki/people/principal.md."

What each file does:
- **`IDENTITY.md` and `SOUL.md`**: the agent's card and its operating self. Tune them now and rarely after.
- **`USER.md`**: your rules for the agent. It's the most important file. Every time you correct the agent, the rule belongs here. Start with:
  - your channels
  - your quiet hours
  - what always needs your confirmation
  - your formatting and voice preferences
  - any standing "never do X" rules
- **`wiki/people/principal.md`**: who you are: role, responsibilities, current priorities, key people. A work profile should also seed `wiki/stakeholders/` and `wiki/projects/`.
- **`wiki/concepts/voice.md`**: needed if you installed `ghostwriter`. Paste 3 to 5 samples of your writing.

## 3. Two sessions: Admin and Ops

The framework splits the agent across two long-lived Claude Code sessions in the same folder:

| Session | Role |
|---|---|
| **Admin** | Your conversation thread. Runs no crons. |
| **Ops** | Runs the heartbeat cron and every scheduled job. It hands anything you need to see to Admin with tags like `[CHECKIN]`, `[FYI]` and `[URGENT]`, so you never see heartbeat traffic. |

Start Ops with the prompt "You are {{AGENT_NAME}} Ops." The SessionStart hook checks the role and tells Ops to create the heartbeat cron if it's missing. Session-scoped crons expire, typically after about 7 days, and the heartbeat recreates them before then. See [docs/heartbeat.md](docs/heartbeat.md).

Optional thread-mode agents (any module can enable it) run as their own sessions:

```bash
claude --agent <slug>
```

You talk to them directly. They put anything proactive in `subagents/<slug>/outbox.md` for Admin to pass on. See `template/subagents/THREADS.md`.

## 4. Hooks

`.claude/settings.json` ships with these hooks:
- **SessionStart**: role and cron check.
- **Stop**: logs the conversation to `memory/conversations/` on a 7-day rolling basis (gitignored), and stamps whether the Ops turn succeeded.
- **UserPromptSubmit**: heartbeat freshness stamps.

All paths come from `config/workspace.json`, which the init script wrote. See [docs/scripts.md](docs/scripts.md).

## 5. Optional pieces

Each optional piece is off until you set it up. Every one is fail-closed: if it isn't configured, nothing happens.

- **Email filter (`scripts/inbox-filter.py`)**:
  - Polls one mailbox with a read-only OAuth scope.
  - Drops anything not on `trusted_senders`, or failing DMARC/DKIM, before any model sees it.
  - For dropped mail, it tells you only the sender address and a count.
  - Mail that passes goes to `inbox-triage`.
- **Scoped send (`scripts/scoped-send-email.py`)**:
  - The single email the agent may send.
  - Sender and recipients are fixed in config.
  - The token has exactly one Gmail scope, `gmail.send`, which is checked on every send and stored in the Keychain.
  - It sends once per date and respects quiet hours.
  - Leave it unconfigured if you don't need outbound email.
- **Messaging bridge (`scripts/agent-messages-*`, `launchd/`)**:
  - A launchd-managed session that reads and sends iMessage.
  - Applies the same allowlist before any model.
  - Needs Full Disk Access for the Messages database.
- **Voice memos (`scripts/transcribe.sh`)**: offline whisper.cpp transcription into `raw/voice/`. Use the medium model when names or numbers matter. Transcripts don't identify speakers.
- **MCP data sources**: modules like `finance-analyst` expect a read-only data MCP. Register it at user scope and keep the token out of the repo.

## 6. Secrets

Never put secrets in plaintext. Store them in the macOS Keychain:

```bash
security add-generic-password -U -s "<agent-short>/<purpose>" -a "<os_user>" -w
```

Record the slot name, never the value, in `TOOLS.md`.

## 7. Day-to-day

Talk to Admin. It reads the bootstrap files every session, logs the day in `raw/journal/`, routes facts to the wiki through the Librarian, and delegates domain work to subagents.

Run a lint when you like ("lint the wiki"). The heartbeat runs a weekly memory cleanup and surfaces missions that haven't moved in 48 hours or more.

When the agent gets something wrong, tell it the rule. Rules you state go in `USER.md`. Lessons the agent learns go in its `MEMORY.md`. That loop is what makes it better over time.

## Work profile tips

- Enable these modules: `meeting-prep`, `project-tracker`, `research`, `ghostwriter`, `inbox-triage`.
- Seed `wiki/stakeholders/` with the 10 to 20 people you work with most, and `wiki/projects/` with what's in flight.
- Check your employer's policy before connecting work email or calendar. Read-only scopes and a strict allowlist are the floor. Keep confidential employer material out of any repo that leaves your work machine.
