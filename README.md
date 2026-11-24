# Agent Assistant Framework

A ready-to-run scaffold for a personal "chief of staff" agent built on Claude Code. One main agent works for one person (the **principal**), remembers across sessions through files, runs a heartbeat on a schedule, delegates to scoped subagents, and keeps a wiki of the principal's world. A deterministic security layer sits in front of every model.

It came out of a long-running real deployment. Everything personal was stripped out. What's left is the architecture, the conventions and the operating lessons that made it work.

Use it for your work life, your personal life, or hand it to someone else to stand up their own.

## What you get

| Layer | Folder (in your workspace) | What it is |
|---|---|---|
| Schema | root `*.md` + `memory/` | Who the agent is, how it operates, what it has learned, the principal's rules for it, heartbeat protocol, operational state |
| Wiki | `wiki/` | The principal's institutionalized world: people, projects, initiatives, concepts. Only the Librarian writes it |
| Subagents | `subagents/` + `.claude/agents/` | Domain-scoped agents with their own identity, scope, rules and memory |
| Raw | `raw/` | Immutable sources: the daily journal, documents, transcripts. Read, never edited |

Plus:
- **Hooks** (`.claude/settings.json`): session-start role check, conversation logging, heartbeat health stamps.
- **Heartbeat**: a cron in a dedicated Ops session runs a checklist every few minutes and only speaks up when something needs the principal.
- **Security model**: a sender allowlist enforced by code before any LLM sees a message, an email DMARC/DKIM check, link safety checks, read-only OAuth scopes, one narrowly scoped send path, quiet hours, and secrets kept in the OS keychain.
- **Value-Interface Schema**: every load-bearing number carries its scope, entity, timestamp and source, so a slice is never cited as a total and an estimate is never cited as fact.

See [docs/architecture.md](docs/architecture.md) for the full picture.

## The wiki

**What it's for.** The wiki is the agent's long-term knowledge of you: your role, your projects, the people you work with, your frameworks and decisions, your history and plans. A chat session forgets everything when it ends, and the wiki is how the agent doesn't. Every session starts from `wiki/index.md` and drills into whatever the conversation needs, so the agent answers from what it already knows about you instead of asking you to explain again.

**How it gets built and maintained.** You don't write it. You talk to the agent, send it documents, and correct it, and the wiki grows out of that:
- When something worth keeping comes up, the agent (or a subagent) proposes a page change as a submission to the Librarian.
- The Librarian is the only writer. It merges each submission into the right page, keeps `index.md` and the change log current, and never deletes: superseded content is archived.
- Every week the heartbeat runs the Librarian, sweeps lasting facts out of the journal and agent memory into submissions, and lints the wiki for contradictions, stale claims and orphan pages.

**It's written for the agent, not for you.** Pages are optimized for an agent to find and trust facts quickly: dense, cross-linked, frontmatter on every page, sources and dates kept next to claims, nothing deleted. You can read it (it opens in any Markdown viewer or Obsidian), but it isn't meant to be pleasant reading and it isn't meant to be hand-edited. If something in it is wrong, tell the agent; it routes the correction through the Librarian so the page, the index and the log stay consistent. A hand edit skips all of that and can be silently overwritten or contradicted by the next integration.

## Modules

`librarian` and `research` are always installed. The rest are optional; pick them in `config.toml`.

| Module | Fits | What it does |
|---|---|---|
| `ghostwriter` | work, personal | Drafts posts and long-form in the principal's voice. Never publishes |
| `inbox-triage` | work, personal | Classifies mail that already passed the allowlist. Read-only |
| `meeting-prep` | work | Builds pre-meeting briefs from the calendar and the wiki |
| `project-tracker` | work | Tracks projects and initiatives, flags stale ones, weekly status |
| `finance-analyst` + `finance-reviewer` | personal | Read-only financial analysis with a mandatory peer-review loop |
| `health-advisor` | personal | Interprets records and labs with tiered evidence and care flags |
| `pet-care` | personal | Veterinary records and care questions |
| `meal-planner` | personal | Weekly menus, recipes, audited shopping lists |
| `price-watch` | personal | Daily price checks on a watch list |

Details in [docs/modules.md](docs/modules.md). New ones are made with the `/new-subagent` command inside your workspace.

## Quick start

Requirements: macOS (the launchd, Keychain and Messages pieces are macOS-specific; the rest runs anywhere), Python 3.9+ (on 3.9 and 3.10, also `pip3 install --user tomli`; the macOS system `python3` works), git, and [Claude Code](https://claude.com/claude-code).

```bash
cp config.example.toml config.toml        # fill it in
python3 bin/init_workspace.py --config config.toml --dest ~/repos/my-agent --dry-run
python3 bin/init_workspace.py --config config.toml --dest ~/repos/my-agent
```

To change a setting later, edit `config.toml` and re-run with `--update-config` (never `--force`, which overwrites your personalized files). See [docs/scripts.md](docs/scripts.md).

Then follow [SETUP.md](SETUP.md): first session, personalizing the identity and user contract, starting the Ops session and heartbeat, and the optional pieces (email filter, messaging bridge, voice transcription).

## Repo layout

```
config.example.toml   the only file you fill in
bin/init_workspace.py instantiates a workspace from template/ + chosen modules
template/             the workspace skeleton (placeholders like {{PRINCIPAL_NAME}})
modules/<slug>/       optional subagents: subagent/, agent.md, MODULE.md
docs/                 architecture, security model, value schema, heartbeat, scripts, modules
```

## Privacy

The framework repo holds no personal data. Your instantiated workspace will, so keep it in a private repo. `config.toml` is gitignored here. The workspace `.gitignore` keeps conversation logs and fetched mail local.
