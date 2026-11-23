# SCOPE: Meeting Prep

## Domain

Pre-meeting briefs from the calendar plus what the workspace already knows about the people, organizations and initiatives involved. Post-meeting capture of decisions and action items when {{PRINCIPAL_NAME}} provides notes.

## Triggers

Invoked by {{AGENT_NAME}} via the Agent tool with `subagent_type: meeting-prep`:

1. **Daily prep** (scheduled, suggested early morning {{TIMEZONE}}, before the first meeting). Prompt: *"Prep today's meetings."* Briefs for today's meetings and for tomorrow's meetings that start before 10:00.
2. **Single meeting** (on demand). Prompt: *"Prep '<meeting title or time>'."*
3. **Debrief** (on demand). Prompt: *"Debrief '<meeting>': <principal's notes>."* Turns notes into decisions, action items and wiki submissions.

## Tools

`Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch`, plus the read-only calendar tools wired at install (and optionally read-only mail search).

## Inputs

| Source | Used for |
|---|---|
| Calendar (read-only) | Title, time, attendees, description, attachments list, recurrence |
| `wiki/people/` | Who each attendee is to {{PRINCIPAL_NAME}}, history, preferences |
| `wiki/clients/`, `wiki/businesses/`, organization pages | The organizations in the room |
| `wiki/initiatives/` | The projects the meeting touches |
| `raw/journal/` (last 14 days) | Recent context and commitments |
| `subagents/meeting-prep/briefs/` | Previous briefs and debriefs with the same people |
| Mail search (optional, read-only) | Recent threads with attendees, subject lines and dates only unless the body is needed |
| Public web | Professional background on outside attendees and organizations |

## Brief depth

| Depth | When | What |
|---|---|---|
| **Full** | First meeting with someone; any outside party with decision power; anything {{PRINCIPAL_NAME}} marked important; interviews, negotiations, reviews | Complete template |
| **Standard** | Recurring meetings with outside parties; internal meetings with senior stakeholders or a decision on the agenda | Purpose, open loops, objectives, one line per key attendee |
| **Line** | Routine internal meetings | One line in the daily index: anything open with these people? |
| **Skip** | Focus blocks, personal events, holds, meetings {{PRINCIPAL_NAME}} declined | Nothing |

## Outputs

| Path | When | What |
|---|---|---|
| `subagents/meeting-prep/briefs/YYYY-MM-DD-index.md` | Each daily run | Today's meetings in order with depth and links to briefs |
| `subagents/meeting-prep/briefs/YYYY-MM-DD-HHMM-<slug>.md` | Each Full or Standard meeting | The brief; a debrief section is appended later |
| `subagents/librarian/submissions/meeting-prep-YYYY-MM-DD-<slug>.md` | A new person or organization worth a wiki page, or a durable fact or decision from a debrief | Submission; never a direct wiki write |
| `subagents/meeting-prep/MEMORY.md` | A cross-meeting lesson | Entry with **Why:** and **How to apply:** |
| `subagents/meeting-prep/memory/active-work.md` | Run start and end | Operational state |
| `subagents/meeting-prep/questions.md` | Blocked on {{PRINCIPAL_NAME}} | Open question |

Nothing else.

## Report back to {{AGENT_NAME}}

```
- task_type: daily-prep | single-meeting | debrief
- index_path: <path or null>
- briefs: [{time, title, depth, path}]
- needs_attention: [<meetings with a conflict, missing agenda, unprepared ask, or an open loop {{PRINCIPAL_NAME}} owes>]
- action_items: [<from a debrief: owner, item, due>]
- submissions: [<paths>]
- source_failures: [<...>]
- notes_for_principal: <...>
```

{{AGENT_NAME}} surfaces `needs_attention` in the morning check-in and logs debrief action items where the workspace tracks them (for example the project-tracker module).
