# projects/: tracker records

One file per tracked project: `<slug>.md`, lowercase and hyphenated, matching the wiki initiative slug when one exists. Closed projects move to `.closed/`.

## Template

```markdown
---
type: project-record
name: <project name>
slug: <slug>
lifecycle: active | waiting | parked | done | killed
health: green | amber | red
owner: <{{PRINCIPAL_NAME}} or another named owner>
priority: <1-N, optional>
due: YYYY-MM-DD | null
next_action: <one concrete step>
waiting_on: <who or what, only if waiting>
stale_after_days: <override, optional>
last_movement: YYYY-MM-DD
last_flagged: YYYY-MM-DD | null
wiki: wiki/initiatives/<slug>.md | null
external: [<tracker or repo links, optional>]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# <Project name>

## Goal
<one or two sentences: what done looks like>

## Milestones
- [ ] <milestone> (due YYYY-MM-DD)

## Log
*(append-only, newest last; every entry cites a source)*
- YYYY-MM-DD: <what moved>. Source: <path, date or ticket>.
```
