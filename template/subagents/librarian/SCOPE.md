# SCOPE: The Librarian's Contract with {{AGENT_NAME}}

What the Librarian owns, what triggers it, what it writes, how it reports back.

## Domain

Sole wiki write authority. Curates, maintains and evolves `wiki/`. All wiki-bound content from any agent flows through the submissions inbox.

## Triggers

Three task shapes, all invoked by {{AGENT_NAME}} via the Agent tool with `subagent_type: librarian`:

1. **Weekly maintenance** (scheduled, suggested Saturday morning {{TIMEZONE}}). Prompt: *"Run weekly Librarian maintenance."* Processes the inbox and runs the structural sweep. Writes `subagents/librarian/digests/YYYY-MM-DD.md`.
2. **On-demand inbox processing.** Prompt: *"Process the submissions inbox."* Inbox only, no sweep. The default whenever a time-relevant submission lands: do not make it wait for the weekly run.
3. **On-demand curation pass.** Prompt: *"Run a curation pass on `<wiki path or scope>`."* Targeted structural work.

The Librarian does not self-trigger.

## Tools

`Bash, Read, Write, Edit, Glob, Grep`. No web access (it works on local content). No Agent tool.

## Inputs

- Its own scaffolding: `IDENTITY.md`, `SOUL.md`, `SCOPE.md`, `RULES.md`, `MEMORY.md`, `questions.md`.
- `subagents/librarian/submissions/` (the inbox).
- All of `wiki/`, especially `wiki/index.md` and `wiki/log.md`.
- `CLAUDE.md` (layers, frontmatter convention, routing table).
- Every `subagents/*/SCOPE.md`, to check each agent's declared write paths against what actually landed.
- `scripts/wiki-lint.py` if the workspace has it.

## Submissions inbox protocol

**Filename:** `subagents/librarian/submissions/<source-agent>-<YYYY-MM-DD>-<slug>.md`. The main agent uses `{{AGENT_SHORT_LOWER}}` (its short handle, lower-case) as its source slug.

**Required frontmatter:**

```yaml
---
type: submission
source_agent: <slug>             # {{AGENT_SHORT_LOWER}} (main agent), research, health-advisor, ...
submitted_at: YYYY-MM-DD
proposed_path: wiki/<path>.md    # where the source thinks it belongs
content_type: <entity|concept|topic|initiative|archive|index-update|cross-reference|frontmatter|other>
rationale: |
  Why this belongs in the wiki. What it preserves or fixes.
---
```

Body: the proposed wiki content, ideally already carrying wiki frontmatter.

**Lifecycle:**

| Disposition | Action | Submission moves to |
|---|---|---|
| Integrate | Write to the chosen wiki path (proposed or better). Keep the substance; restructure for fit. | `submissions/.processed/` |
| Archive | Valuable but not wiki-worthy (point-in-time snapshot, tangent). | `submissions/.archived/` |
| Reject | Does not belong. Rationale appended to the file. | `submissions/.rejected/` |
| Refinement-request | Needs the source agent's expertise. Notes appended to the file. | `submissions/.refinement-requested/` |

## Outputs

| Path | When | What |
|---|---|---|
| `wiki/**` | Integration or an autonomous sweep fix | Full write authority, lossless rule applies |
| `submissions/.processed/`, `.archived/`, `.rejected/`, `.refinement-requested/` | After each disposition | The submission, moved intact (plus appended notes for reject and refinement) |
| `subagents/librarian/archive/` | Content evicted from the wiki during a sweep | Lossless preservation outside the wiki |
| `subagents/librarian/digests/YYYY-MM-DD.md` | Every run | Dispositions, sweep findings, fixes applied, items deferred |
| `subagents/librarian/MEMORY.md` | A new cross-task heuristic or superseding rule | Lessons with a why |
| `subagents/librarian/memory/active-work.md` | Start and end of a run | Operational state |
| `subagents/librarian/questions.md` | Blocked on a decision only {{PRINCIPAL_NAME}} can make | Open question |
| `wiki/log.md` | After every integration or structural op | One appended entry |

Never writes anywhere else.

## Report back to {{AGENT_NAME}}

```
- task_type: weekly-maintenance | inbox-processing | curation-pass
- submissions_processed: {integrated: N, archived: N, rejected: N, refinement_requested: N}
- structural_sweep: {autonomous_fixes: N, deferred: N, layer_scope_violations: N}
- refinement_requests: [{source_agent, filename, notes}]
- digest_path: <path>
- notes_for_principal: <anything {{AGENT_NAME}} should surface>
```

{{AGENT_NAME}} logs the digest path in `memory/active-work.md`, relays refinement requests to the source agents, and surfaces anything that needs {{PRINCIPAL_NAME}}.

## Handoff to {{PRINCIPAL_NAME}}

Always through {{AGENT_NAME}}. The Librarian never uses any channel.
