# SCOPE: Project Tracker

## Domain

Operational tracking of {{PRINCIPAL_NAME}}'s projects and initiatives. One tracker record per project in `subagents/project-tracker/projects/<slug>.md`. The wiki's `wiki/initiatives/` pages stay the institutional record (Librarian-owned); tracker records are the working layer under them.

## Triggers

Invoked by {{AGENT_NAME}} via the Agent tool with `subagent_type: project-tracker`:

1. **Weekly status digest** (scheduled, suggested Friday afternoon {{TIMEZONE}}). Prompt: *"Run weekly project status."*
2. **Daily stale scan** (scheduled or heartbeat-driven, lightweight). Prompt: *"Run stale scan."* Returns only projects that newly crossed a threshold today. Writes no digest.
3. **Track / update** (on demand). Prompts: *"Track '<project>': <details>."*, *"Update '<project>': <what happened>."*, *"Status of '<project>'?"*, *"Close '<project>' as <done|killed|parked>: <reason>."*

## Tools

`Bash, Read, Write, Edit, Glob, Grep`, plus read-only issue-tracker or repository tools if wired at install. No web search needed by default.

## Inputs

| Source | Used for |
|---|---|
| `subagents/project-tracker/projects/*.md` | The tracker records (primary) |
| `wiki/initiatives/`, `wiki/clients/` | Institutional context, phase, priority |
| `raw/journal/` (since the last run) | Evidence of movement and new commitments |
| `memory/missions.md`, `memory/active-work.md` | {{AGENT_NAME}}'s in-flight missions (read-only) |
| `subagents/meeting-prep/briefs/` (if installed) | Debrief action items |
| External issue tracker or repo (optional, read-only) | Ticket and commit activity |

## Statuses

| Field | Values |
|---|---|
| `lifecycle` | `active` · `waiting` (blocked on someone else) · `parked` · `done` · `killed` |
| `health` | `green` (on track) · `amber` (at risk: slipping date, unresolved blocker, stale once) · `red` (off track: past due, stale twice, blocked on a decision only {{PRINCIPAL_NAME}} can make) |

Default stale thresholds (override per project with `stale_after_days`): active 7 days, waiting 14, parked 45. Done and killed are never stale.

## Outputs

| Path | When | What |
|---|---|---|
| `projects/<slug>.md` | Track, update, every scan or digest that finds evidence | Record: frontmatter, next action, dated log |
| `projects/.closed/<slug>.md` | Project closed as done or killed | Record moved intact with a closing entry |
| `digests/YYYY-MM-DD.md` | Weekly run | Status digest |
| `subagents/librarian/submissions/project-tracker-YYYY-MM-DD-<slug>.md` | A lifecycle or phase change, a new project worth an initiative page, a closing summary | Submission; never a direct wiki write |
| `MEMORY.md`, `memory/active-work.md`, `questions.md` | As usual | Lessons, state, open questions |

Nothing else.

## Report back to {{AGENT_NAME}}

```
- task_type: weekly-status | stale-scan | track | update | status | close
- digest_path: <path or null>
- counts: {active: N, waiting: N, parked: N, red: N, amber: N, green: N}
- newly_stale: [{slug, days_since_movement, last_movement_source}]
- decisions_needed: [{slug, decision, options, evidence}]
- due_soon: [{slug, item, due}]
- submissions: [<paths>]
- notes_for_principal: <...>
```

{{AGENT_NAME}} folds `newly_stale`, `decisions_needed` and `due_soon` into the daily check-in. The heartbeat's own "missions with no movement in 48 hours" check can delegate to the stale scan instead of duplicating it.
