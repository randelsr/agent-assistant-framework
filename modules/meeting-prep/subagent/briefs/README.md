# briefs/

Daily indexes and per-meeting briefs. Kept indefinitely: the next brief with the same people reads the last one.

## Naming

- Daily index: `YYYY-MM-DD-index.md`
- Brief: `YYYY-MM-DD-HHMM-<slug>.md` (local time, {{TIMEZONE}})

## Brief template

```markdown
---
type: meeting-brief
date: YYYY-MM-DD
time: HH:MM
title: <calendar title>
depth: full | standard
attendees: [<names>]
related: [<wiki paths>]
---

# <Title>: YYYY-MM-DD HH:MM

**Why this meeting:** <one line>
**Who matters:** <names and one-word role>
**Walk out with:** <1-3 objectives>

## Attendees
- **<Name>**, <role, organization>. Last interaction: <date, what, source>. Cares about: <...>. Open threads: <...>.

## Context
<related initiatives, last decisions, recent journal mentions, each sourced>

## Open loops
- {{PRINCIPAL_NAME}} owes: <item, since when, source>
- They owe: <item, since when, source>

## Questions to ask

## Sensitivities
<anything to handle with care>

## Sources

## Debrief
*(appended after the meeting from {{PRINCIPAL_NAME}}'s notes)*
- Decisions:
- Action items: <owner, item, due>
- Follow-ups:
```

## Daily index template

```markdown
# Meetings: YYYY-MM-DD

| Time | Title | Depth | Brief | Flag |
|---|---|---|---|---|
```
