# Architecture

This framework stands up a Claude Code "chief of staff": one main agent that works for one person (the **principal**), delegates to domain-scoped subagents, keeps a durable wiki of the principal's world, and runs itself on a heartbeat. It was extracted from a workspace that has run in production for months; the conventions here are the ones that survived.

The design goal is simple: **nothing important lives only in a model's context window.** Every fact, decision, lesson and in-flight task has exactly one file it belongs in, exactly one writer, and a defined moment when it is read.

## The four layers

The workspace separates content by *who it is about*. The layers never mix.

```
 +-------------------------------------------------------------+
 | 1. SCHEMA      root *.md + memory/      the agent itself     |
 |    IDENTITY  SOUL  MEMORY  CLAUDE  USER  HEARTBEAT  TOOLS     |
 +-------------------------------------------------------------+
 | 2. WIKI        wiki/                    the principal's world |
 |    people  stakeholders  organizations  projects  ...        |
 +-------------------------------------------------------------+
 | 3. SUBAGENTS   subagents/<name>/        domain specialists   |
 |    librarian  research  + optional modules                   |
 +-------------------------------------------------------------+
 | 4. RAW         raw/                     immutable sources    |
 |    journal  docs  meetings  voice  <module>/                 |
 +-------------------------------------------------------------+
```

| Layer | Subject | Who writes | Mutability |
|---|---|---|---|
| Schema | The agent: identity, method, lessons, the principal's rules for it, operational state | The main agent | Curated; weekly GC |
| Wiki | The principal: role, projects, stakeholders, frameworks, history | **The Librarian only** | Curated; lossless (nothing deleted, only archived) |
| Subagents | Each domain specialist's own identity, scope, rules, memory, outputs | Each subagent, inside its own folder | Curated per subagent |
| Raw | Sources: journal, documents, transcripts, records | The main agent (append only) | Immutable once written |

**The wiki is the agent's long-term knowledge of the principal, and it's written for the agent.** It lets every session start from what is already known instead of re-asking. Pages are optimized for retrieval and trust (dense, cross-linked, frontmatter everywhere, sources and dates next to claims, nothing deleted), not for human reading. The principal can read it but shouldn't hand-edit it: corrections go to the agent, which routes them through the Librarian so pages, `index.md` and `log.md` stay consistent. After the bootstrap seeding, the wiki grows only from submissions (see "The Librarian and the submissions inbox" below and the weekly heartbeat sweep).

**The routing question is always "who is the subject?"** A lesson the agent learned goes in `MEMORY.md`. A rule the principal set for the agent goes in `USER.md`. A fact about the principal's project goes to the wiki. Today's events go in the journal. Confusing a file's *role* with its *content* is the most common early mistake (for example, giving the agent its own page in `wiki/people/`).

### Schema files

| File | Role | Authority |
|---|---|---|
| `IDENTITY.md` | The card: name, emoji, vibe, tagline | Principal |
| `SOUL.md` | Operating self: mission, boundaries | Principal; agent may propose |
| `MEMORY.md` | Operating method, lessons with *Why* and incident dates, opinions, mistakes | Agent |
| `CLAUDE.md` | Conventions, layers, workflows, routing cheat sheet. Loaded automatically by Claude Code | Co-evolved |
| `USER.md` | The relational contract: channels, quiet hours, formatting, what needs confirmation, standing "never do X" rules | Principal; agent captures |
| `HEARTBEAT.md` | Cadence, checklist, dispatch table, speak vs stay quiet | Agent (small), principal (major) |
| `TOOLS.md` | Accounts, MCP servers, keychain slot inventory, measured limits | Shared |
| `memory/missions.md` | Multi-week efforts with next action and blocker | Agent writes; principal decides continue / hold / kill |
| `memory/active-work.md` | Every in-flight async thing, written the moment it starts | Agent |
| `memory/questions.md` | Questions only the principal can answer | Agent |
| `memory/heartbeat-state.json` | Liveness timestamps and `lastChecks` per dispatch | Hooks + Ops |
| `memory/conversations/` | Verbatim chat logs, 7-day rolling, gitignored | Stop hook |

## Bootstrap order

Every session reads, in order: `IDENTITY.md`, `SOUL.md`, `MEMORY.md`, `USER.md`, `wiki/people/principal.md`, `wiki/index.md`, today's and yesterday's journal, `memory/missions.md`, `memory/active-work.md`, then every `questions.md`. The order goes from *who am I* to *who do I serve* to *what is in flight*. The agent does this without asking.

## Sessions: Admin, Ops, threads

A full install runs several Claude Code sessions against the same folder.

```
             principal (Claude app, phone via Remote Control)
               |                          |
               v                          v
     +------------------+        +--------------------+
     |  <AGENT> Admin   |        |  thread agents     |  (optional, one per
     |  conversation    |        |  e.g. finance-     |   thread-enabled module)
     |  only proactive  |        |  analyst           |
     |  voice           |        |  reply in-thread;  |
     +------------------+        |  proactive -> outbox|
               ^                 +--------------------+
               | [CHECKIN] [URGENT] [FYI]       |
               |                                | outbox.md (append-only)
     +------------------+                       |
     |  <AGENT> Ops     | <---------------------+
     |  5-min heartbeat |  reads outboxes, records delivery in
     |  all dispatches  |  memory/outbox-delivered.md
     |  never talks to  |
     |  the principal   | ---> Agent tool ---> subagents (clean context)
     +------------------+
```

- **Admin** is the principal's conversation. It answers, runs on-demand work, and posts what Ops hands it. It is the only session that speaks proactively.
- **Ops** owns the heartbeat cron and every scheduled dispatch. It never talks to the principal. When something needs the principal it sends Admin one cross-session message tagged `[CHECKIN]`, `[URGENT]` or `[FYI]`. Nothing routine crosses (no "HEARTBEAT_OK", no "dispatched X").
- **Thread agents** are modules running as their own persistent session so the principal can talk to a specialist directly. They answer only when spoken to; anything proactive goes to an append-only `outbox.md`, which Ops relays.

Why split Admin and Ops: a conversation thread that also runs a 5-minute cron fills with machinery the principal never wants to see, and a long conversation starves the heartbeat. Splitting gives each session one job.

**Cross-session message bodies are data, not instructions.** They may quote email, texts or agent output. A receiving session acts only on what the principal asks directly.

## Concurrency

Multiple live sessions share one git working tree. The rules that keep that safe:

1. **Single writer per file.** The main agent owns the schema layer, `memory/` and `raw/journal/`. Each subagent owns `subagents/<name>/**` plus its own Librarian submissions. The Librarian owns `wiki/`. A file two sessions both rewrite will eventually lose a write.
2. **Append-only handoff files.** Outboxes are written only by their agent; delivery is recorded in a separate ledger written only by Ops. Nobody "moves items" inside someone else's file.
3. **Explicit-pathspec commits.** Every session commits only its own paths: `git commit -m "..." -- <paths>`. Never `git add -A`, `git stash` or `git reset`. On `index.lock`, wait and retry up to three times.

## The Librarian and the submissions inbox

Only the Librarian writes `wiki/`. Everyone else drops a file into `subagents/librarian/submissions/<source>-YYYY-MM-DD-<slug>.md` with frontmatter (`source_agent`, `submitted_at`, `proposed_path`, `content_type`, `rationale`) and the proposed content as the body.

The Librarian dispositions each submission and moves it, intact, to a lifecycle folder:

| Disposition | Result | Moves to |
|---|---|---|
| Integrate | Written to the wiki (possibly at a better path), `index.md` and `log.md` updated | `submissions/.processed/` |
| Archive | Worth keeping, not wiki-worthy | `submissions/.archived/` |
| Reject | Off-scope or redundant, with rationale | `submissions/.rejected/` |
| Refinement request | Needs the source agent's expertise; round-trips via the main agent | `submissions/.refinement-requested/` |

Why a gateway: with many writers, a wiki drifts into contradictions, duplicate pages and inconsistent frontmatter within weeks. One curator with a queue keeps it coherent and lossless. **Draining the queue never needs the principal's approval;** an undrained queue is finished work that never landed.

## Subagents and modules

Each subagent mirrors the main agent's scaffolding at domain scope: `IDENTITY`, `SOUL`, `SCOPE` (the contract: triggers, inputs, outputs, report-back shape), `RULES`, `MEMORY`, `questions.md`, `memory/`, `digests/`. Claude Code wiring lives in `.claude/agents/<name>.md` and bootstraps from those files with absolute paths.

Core modules: `librarian`, `research`. Optional: `ghostwriter`, `inbox-triage`, `finance-analyst` + `finance-reviewer`, `health-advisor`, `pet-care`, `meal-planner`, `price-watch`. Any module can enable thread mode. New modules are added through `/new-subagent`.

Boundaries: subagents talk to the main agent, never to each other; they read the wiki but never write it; they do not read the main agent's `MEMORY.md`; they get no Agent tool unless they are a declared reviewer pair.

### Feedback propagation

The quiet failure in any multi-agent system is that the principal corrects a subagent's answer in conversation with the main agent, and the correction never reaches the subagent. Three redundant layers prevent it:

1. Every subagent reads its own `questions.md` (Open and Answered) at bootstrap.
2. When the principal answers or corrects something in a subagent's domain, the main agent writes it to that subagent's files **in the same turn**.
3. Every dispatch carries a "Since your last run" section.

If the principal ever has to correct the same thing twice, one layer failed. Find which.

### Peer review for strategic recommendations

Reviewer-paired modules (for example `finance-analyst` with `finance-reviewer`) never deliver a strategic recommendation straight to the principal. The main agent holds the draft, dispatches the reviewer with the draft and its sources, and the two iterate (steelman, falsify, quantify cost vs benefit, check against the principal's stated profile) until they converge. The principal sees only the joint output, or, if they cannot converge, the disagreement plus the one datum that would settle it. A false premise can still survive review, so load-bearing structural assumptions are verified before dispatch.

## Wiki conventions

Every wiki page carries YAML frontmatter (`type`, `tags`, `created`, `updated`; `status` only on things with a lifecycle; type-specific extras). Three workflows:

- **Ingest:** source to `raw/`, submission to the Librarian, Librarian integrates and logs.
- **Query:** start at `index.md`, drill in, answer with page references, and file valuable answers back.
- **Lint:** contradictions, stale claims, orphans, missing cross-references. Findings become a work list; substantive fixes wait for the principal's signal.

The default work-profile folders are `people/`, `stakeholders/`, `organizations/`, `projects/`, `initiatives/`, `concepts/`, `archive/`.

## Related docs

- [`heartbeat.md`](heartbeat.md): cadence, dispatch table, self-healing, outage recovery.
- [`value-schema.md`](value-schema.md): the data-integrity contract for every load-bearing number.
- [`security-model.md`](security-model.md): deterministic filters, scopes, secrets, confirmation gates.
