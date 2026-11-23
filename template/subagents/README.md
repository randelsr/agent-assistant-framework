# subagents/: The Subagent Framework

Scoped agents that {{AGENT_SHORT}} (the orchestrator) delegates to. Each subagent owns one domain, has its own scaffolding, and reports back to {{AGENT_SHORT}}. The principal talks to subagents directly only when a module runs in thread mode ([`THREADS.md`](THREADS.md)).

## Architecture

```
{{AGENT_SHORT}} (orchestrator, root scaffolding)
  | delegates via the Agent tool (subagent_type: <name>)
  v
Subagent (clean context, reads its own scaffolding, executes, returns)
  | reports back via the Agent return value + persistent file outputs
  v
{{AGENT_SHORT}} (verifies, integrates, surfaces to the principal)
```

**Boundaries:**

- Subagents talk to {{AGENT_SHORT}}. They never talk to the principal directly, except in thread mode, and even then never proactively (proactive items go to their `outbox.md`).
- Subagents talk to each other only via {{AGENT_SHORT}}. No direct cross-subagent communication. The one exception is a declared reviewer pair (for example `finance-analyst` consulting `finance-reviewer` in thread mode), and only when the module says so.
- Subagents read `wiki/` freely. They write only inside their own scope (`SCOPE.md`).
- **Wiki write authority belongs to the Librarian only.** Every other agent proposes wiki content via `subagents/librarian/submissions/<source>-YYYY-MM-DD-<slug>.md`. The Librarian gates entry, shapes it and integrates it.
- Subagents keep their own `MEMORY.md`. They do not read {{AGENT_SHORT}}'s `MEMORY.md`.
- Subagents get no Agent tool by default (no recursive delegation), except reviewer-paired modules.

## Per-subagent scaffolding

Mirror of the orchestrator pattern, scoped to one domain:

| File | Why it exists | Edited by |
|------|---------------|-----------|
| `IDENTITY.md` | Card: name, domain, vibe, emoji, "reports to {{AGENT_SHORT}}" | Principal + {{AGENT_SHORT}} |
| `SOUL.md` | Voice, stance, what good output looks like in this domain | Principal + {{AGENT_SHORT}} |
| `SCOPE.md` | The contract: domain, triggers, tools, inputs, outputs (paths), report-back shape | Principal + {{AGENT_SHORT}} |
| `RULES.md` | Numbered operational rules: hard "never X", soft defaults, failure modes, quality tiers | Principal + {{AGENT_SHORT}}; the subagent may propose |
| `MEMORY.md` | Cross-task learnings in the domain | The subagent |
| `questions.md` | Its open questions to the principal (`## Open` / `## Answered` / `## Withdrawn`), read at every bootstrap | The subagent; {{AGENT_SHORT}} moves answered items in the same turn the principal answers |
| `outbox.md` | Thread-mode only: proactive items for {{AGENT_SHORT}} to surface | The subagent, append-only |
| `memory/active-work.md` | In-flight task pointers | The subagent |
| `digests/` | Dated run outputs (`YYYY-MM-DD.md`) | The subagent |
| Domain dirs | Whatever the work needs (`topics/`, `records/`, `drafts/`) with a README each | The subagent |

## Claude Code wiring (`.claude/agents/<name>.md`)

A thin definition: frontmatter (`name`, `description`, `tools`) plus a body that tells the subagent to:

1. Bootstrap by reading `{{WORKSPACE_PATH}}/subagents/<name>/{IDENTITY,SOUL,SCOPE,RULES,MEMORY}.md` and `questions.md`.
2. Read its domain config (for example every file in `topics/`).
3. Operate within scope.
4. Return a structured summary; write persistent outputs to the paths declared in `SCOPE.md`.

Use absolute paths in the bootstrap list so the agent works from any working directory.

## Delegation pattern

1. **Confirm scope match.** Read `SCOPE.md` if uncertain.
2. **Delegate** with an explicit brief: what to do, what to write, what to return, plus a **"Since your last run"** section (answered questions, corrections, new context). The subagent has a clean context; brief it like a colleague who just walked in.
3. **Verify the return** (relay gates in {{AGENT_SHORT}}'s `MEMORY.md`), then integrate.
4. **Peer review** strategic recommendations from reviewer-paired modules before relaying.
5. **Cross-domain follow-up** is initiated by {{AGENT_SHORT}}, never by the subagent.

## Modules

Core modules are always installed. Optional modules are chosen in `config.toml` (`[modules] enabled`). Any module can enable thread mode.

| Slug | Domain | Core? | Typical trigger | Notes |
|------|--------|-------|-----------------|-------|
| `librarian` | Sole wiki writer. Drains the submissions inbox, runs structural sweeps, keeps the wiki lossless | Core | Weekly + on demand | Never asks permission to drain its queue |
| `research` | Weekly research digests on configured topics; baselines new topics | Core | Weekly + on demand | Submits durable findings to the Librarian |
| `ghostwriter` | Drafts content in the principal's voice (posts, articles, external email drafts) | Optional | On demand | Never publishes; no em dashes in public content |
| `inbox-triage` | Classifies already-filtered email as urgent / agenda / ignore; extracts dates and asks | Optional | Heartbeat | Read tool only; never acts |
| `finance-analyst` | Financial analysis and advisory; read-only on financial data | Optional | Weekly + on demand | Strategic recs gated by `finance-reviewer`; never moves money |
| `finance-reviewer` | Independent dialectical peer for `finance-analyst` recommendations | Optional (pairs) | On each strategic rec | Read-only |
| `health-advisor` | Health and fitness interpretation with tiered evidence and explicit care flags | Optional | Monthly + on demand | Not a clinician; flags care, never prescribes |
| `pet-care` | Animal health records, check-ins and care flags | Optional | Weekly + on demand | Flags care, never prescribes |
| `meal-planner` | Weekly menus, recipes, shopping lists with an ingredient audit | Optional | Weekly | Never orders or buys |
| `price-watch` | Daily price checks on tracked items | Optional | Daily | Surfaces qualified hits only; never buys |

## Installed subagents

*(Updated by `/new-subagent` and by the init script.)*

| Name | Domain | Thread mode | Status |
|------|--------|-------------|--------|
| `librarian` | Wiki gateway | No | Active |
| `research` | Research digests | No | Active |

## Adding a new subagent

Use the `/new-subagent` slash command:

```
/new-subagent <slug>
```

It reads this README and an existing module as the reference, runs the design conversation with the principal (identity, scope, rules, tools, cadence, thread mode), confirms the design, materializes the scaffolding and `.claude/agents/<slug>.md`, adds a dispatch-table row to `HEARTBEAT.md` if the module runs on a schedule, registers it here and in the wiki (via the Librarian), and validates. Full command body: `.claude/commands/new-subagent.md`.

**Always principal-and-{{AGENT_SHORT}}-led.** The principal shapes the design in conversation; {{AGENT_SHORT}} writes the files.
