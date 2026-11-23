---
type: framework
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Agent threads: the direct-conversation contract

Any module can run in **thread mode**: a persistent session the principal talks to directly, alongside its normal subagent mode. The governing rule: **agents message the principal only through {{AGENT_SHORT}}, unless they are being spoken to.**

## Two modes, one agent

Thread-enabled agents are listed in `subagents/README.md` ("Installed subagents", Thread mode = Yes). Every other agent stays subagent-only.

| | Subagent mode | Thread mode |
|---|---|---|
| How it starts | {{AGENT_SHORT}} calls the Agent tool (scheduled runs, routed questions) | A Claude Code session started as the agent (`claude --agent <name>`), which the principal talks to directly, often from the Claude app via Remote Control |
| Who you answer | {{AGENT_SHORT}}, via your structured return | **The principal, conversationally, in this thread** |
| Proactive messages to the principal | Never | **Never.** Write them to your outbox; {{AGENT_SHORT}} surfaces them. |
| Output format | Structured summary per `SCOPE.md` | Natural conversation. Still write digests and records to files when the work is substantive. |

How to tell which mode you are in: if your first input is a dispatch prompt (Agent tool, "Run weekly...", a structured brief), you are in subagent mode. If a human is chatting with you in a live session, you are in thread mode.

## Thread-mode rules

1. **Bootstrap as usual** from your scaffolding files, then also read `USER.md`. Its behavioral rules bind you in thread mode exactly as they bind {{AGENT_SHORT}}: formatting rules, Value-Interface tags on every load-bearing number, quiet hours, declined-asks-stay-declined, don't chase. You still do **not** read {{AGENT_SHORT}}'s `MEMORY.md`.
2. **Talk only in this thread.** No email, chat apps or any other channel. The principal opening the thread is the only way you speak to them.
3. **Outbox for anything proactive.** Todos for the principal, decisions you need, reminders, alerts and cross-domain flags go in `subagents/<you>/outbox.md`. {{AGENT_SHORT}} reads every outbox and routes cross-domain items. Never message another agent directly; {{AGENT_SHORT}} is the switchboard.
4. **Reviewer-paired modules: review before strategic calls.** If your module has a declared reviewer, run any strategic recommendation past it and converge before giving it to the principal. If the principal wants a quick read, say it is unreviewed and label it that way.
5. **Same scope, same rules.** Your `SCOPE.md` write boundaries, `RULES.md` and the Librarian-only wiki rule are unchanged. Thread mode changes who you talk to, not what you may touch.
6. **Files are memory; the thread is disposable.** Anything that must survive goes to your files (records, digests, `memory/active-work.md`, `MEMORY.md`, `questions.md`). The principal may restart or compact the thread at any time.
7. **Log what the principal tells you.** Facts, decisions and answers go to your own records the same turn, plus a one-line `## For {{AGENT_SHORT}}` item in your outbox so anything cross-domain can be mirrored. Answers to your own Open questions: move them to `## Answered` yourself.

## File ownership (concurrency)

Several sessions share one working folder. To avoid overwrites:

- **You write only your own scope:** `subagents/<you>/**` plus Librarian submissions named `subagents/librarian/submissions/<you>-*.md`. Everything else is read-only to you.
- **{{AGENT_SHORT}}-only files (never write them):** `raw/journal/`, `memory/`, `MEMORY.md`, `USER.md`, `CLAUDE.md`, `HEARTBEAT.md`, `TOOLS.md`. Raw sources the principal hands you in thread go to your own scope; tell {{AGENT_SHORT}} via the outbox if they belong in `raw/`.
- **Wiki:** Librarian only.
- **Commits:** commit only your own paths, with an explicit pathspec: `git add <your paths> && git commit -m "..." -- <your paths>`. If git reports `index.lock`, wait a few seconds and retry (up to 3 times). Never `git add -A`, never commit other agents' files, never stash or reset.

## Outbox format

**Your outbox is append-only, and you are its only writer.** {{AGENT_SHORT}} never edits it; delivery is recorded in {{AGENT_SHORT}}'s ledger, `memory/outbox-delivered.md`. (A shared file that two sessions both rewrite will eventually lose a write. Single writer per file, always.)

Give every item a unique id: `#<agent>-<YYYYMMDD>-<HHMM>`, local time ({{TIMEZONE}}).

```
## For {{PRINCIPAL_NAME}} ({{AGENT_SHORT}} surfaces these)
- [YYYY-MM-DD #<agent>-YYYYMMDD-HHMM] <todo / decision needed / reminder>, <urgency: urgent | today | this week | whenever>

## For {{AGENT_SHORT}} (routing / mirroring)
- [YYYY-MM-DD #<agent>-YYYYMMDD-HHMM] <cross-domain flag or fact {{AGENT_SHORT}} should know>, <target: agent or file>

## Delivered
```

- **Mark urgency honestly.** Ops scans for `urgent` / `today` items on every heartbeat (within about 5 minutes). Everything else waits for the morning check-in.
- **Never edit or delete an item after writing it.** If something changes, append a new item that references the old id.
- **Housekeeping is yours:** once an item's id appears in `memory/outbox-delivered.md`, you may move it to your own `## Delivered`. Prune `## Delivered` entries older than 14 days.

## Hosting

Recommended: each thread agent is a persistent session in the Claude desktop app with Remote Control on, reachable from a phone. Alongside them run **{{AGENT_SHORT}} Admin** (the principal's main conversation thread) and **{{AGENT_SHORT}} Ops** (heartbeat and scheduled-dispatch owner, never talks to the principal).

- If the app cannot pass `--agent`, start the session with a bootstrap prompt that tells it to read and fully adopt `.claude/agents/<name>.md`. Tool limits are then honored by instruction, not enforced; prefer `--agent` where available.
- Thread sessions never create crons and skip the heartbeat self-heal. Only Ops runs the heartbeat.
- If the host machine sleeps or the app quits, the threads go offline until it is back. Ops liveness is checked from Admin (see `HEARTBEAT.md`).
