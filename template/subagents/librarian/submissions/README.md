# submissions/: the wiki inbox

**All wiki-bound content from any agent flows through here.** The Librarian is the only wiki writer. Agents submit; the Librarian decides.

## Filename

```
<source-agent>-<YYYY-MM-DD>-<slug>.md
```

Examples: `research-2025-01-06-topic-update.md`, `main-2025-01-06-new-client.md`, `project-tracker-2025-01-06-status-roll-up.md`.

## Required frontmatter

```yaml
---
type: submission
source_agent: <slug>             # main, research, health-advisor, project-tracker, ...
submitted_at: YYYY-MM-DD
proposed_path: wiki/<path>.md    # the Librarian may choose a better one
content_type: <entity|concept|topic|initiative|archive|index-update|cross-reference|frontmatter|other>
rationale: |
  Why this belongs in the wiki. What it preserves or fixes.
---
```

Body: the content to integrate, ideally with wiki frontmatter at the top (see `CLAUDE.md`).

## Lifecycle

| State | Location | Meaning |
|---|---|---|
| Active | this directory | Waiting for the next run |
| Processed | `.processed/` | Integrated into `wiki/`; kept as a record of the decision |
| Archived | `.archived/` | Valuable but not wiki-worthy; preserved |
| Rejected | `.rejected/` | Does not belong; rationale appended |
| Refinement-requested | `.refinement-requested/` | Source agent must fix something; notes appended |

## When to submit

Any time an agent has content that belongs in the principal's institutional record: a research finding that extends a topic page, a record extraction, a project status change, a new person or organization the principal works with.

## When not to submit

Operational state and working notes (`subagents/<name>/MEMORY.md`, `digests/`, domain folders). Those stay in the agent's own folder.

## Refinement loop

1. The Librarian moves the file to `.refinement-requested/` and appends notes.
2. The digest lists the request.
3. {{AGENT_NAME}} relays it to the source agent.
4. The source agent submits a new file with the same `proposed_path`.
5. The Librarian processes it on the next run.

No agent talks to another directly. {{AGENT_NAME}} is the relay.
