# digests/

One file per weekly status run: `YYYY-MM-DD.md`. Kept indefinitely; together they are the history of what moved and what stalled.

## Format

```markdown
---
type: project-status-digest
date: YYYY-MM-DD
active: N
waiting: N
parked: N
red: N
amber: N
generated_by: project-tracker
---

# Project Status: YYYY-MM-DD

## Red
- **<project>**: <why red>. Last moved <date> (<source>). Suggested: <action or decision>.

## Decisions needed from {{PRINCIPAL_NAME}}
- **<project>**: <decision>. Options: <a / b>. Evidence: <...>.

## Amber
- **<project>**: <why>. Next action: <...>.

## Due in the next 14 days
- <date>: <project>: <item> (owner)

## Green
- <project>: <next action> (owner, due). Last moved <date>.

## Closed this week
- <project>: done | killed. <one-line outcome>.

## Untracked work spotted
- <journal mention, date>: track it?

## Parked
N parked. Review due: <list or "none">.
```

## Calm week

```markdown
# Project Status: YYYY-MM-DD

Everything active moved this week. Due soon: <list or "nothing">.
```
