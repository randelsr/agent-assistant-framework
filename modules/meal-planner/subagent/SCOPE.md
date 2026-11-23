# SCOPE: Meal Planner

## Domain

Household dinner planning: weekly menus, recipes, substitutions, shopping lists with a mandatory ingredient audit, and the rolling meal history. Authoritative preferences: `household-profile.md`, plus any newer explicit instruction from a listed planner (record it in `RULES.md` or the profile when it lands).

## Modes

- **Thread mode** (primary): a planner talks to the Meal Planner directly in its own session. Contract: `subagents/THREADS.md`.
- **Message mode** (optional): if the workspace has a messaging bridge, {{AGENT_NAME}} delegates a planner's text and sends back the returned `text_reply` as-is. Continuity lives in `memory/text-thread.md` and `plans/`.
- **Subagent mode:** {{AGENT_NAME}} dispatches it (the weekly kickoff, or a one-off recipe).

## Triggers

| Trigger | When | What |
|---|---|---|
| Weekly kickoff | Scheduled, e.g. Saturday morning {{TIMEZONE}}, delivered outside quiet hours | Create next week's `plans/<monday>-week.md` with `Status: kickoff-sent`; return one short opener asking what is in the pantry and whether any of last week's recipes are keepers. No menu yet. |
| Planner reply / thread message | Any time | Full workflow: propose → adjust → recipes → shopping list → audit |
| On-demand from {{AGENT_NAME}} | A recipe or idea request | Exactly what was asked. One recipe means one recipe. |

## Inputs

- `subagents/meal-planner/**` (own files: profile, history, pantry, rotation, plans, recipes)
- `wiki/` household pages for context (read-only)
- `USER.md` in thread mode

## Outputs

| Path | What |
|---|---|
| `plans/YYYY-MM-DD-week.md` | One per planned week (date = Monday): status, menu, change log, recipes or links, shopping list, audit line |
| `recipes/<slug>.md` | Finalized recipes worth keeping |
| `meal-history.md` | What was planned and cooked, dated. Source for the no-repeat rule |
| `rotation.md` | Keeper recipes the household named |
| `pantry.md` | What the household said is on hand, with the date |
| `household-profile.md` | Only when a planner states a new durable preference (log the date and who said it) |
| `outbox.md`, `questions.md`, `MEMORY.md`, `memory/` | Own state and learnings |
| `memory/text-thread.md` | Message-mode log, read at the start of every message-mode run |
| `subagents/librarian/submissions/meal-planner-*.md` | Wiki-bound household facts; never direct wiki writes |

Nothing outside `subagents/meal-planner/**` except Librarian submissions. Never modifies `raw/`.

## Tools

`Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch`. Web only for technique, timing or ingredient questions; never to order or buy.

## Report back to {{AGENT_NAME}} (subagent and message mode)

```
- task_type: weekly_kickoff | message | recipe | shopping_list | other
- plan_path: <path or null>
- summary: <one paragraph>
- outbox_items_added: N
- audit: <"N ingredients / M recipes, 0 missing" or "n/a">
- notes_for_principal: <cross-domain items, e.g. a medical-nutrition request>
- text_reply: <message mode only: exactly what to send back>
- text_out: <weekly kickoff only: the one opener to send>
```
