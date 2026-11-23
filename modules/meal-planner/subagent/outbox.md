---
type: outbox
agent: meal-planner
---

# meal-planner outbox

Thread-mode contract: `subagents/THREADS.md`. {{AGENT_NAME}} reads this when building the daily check-in and routes anything cross-domain. This agent is the only writer of this file; it is append-only.

Every item gets a unique id `#meal-planner-YYYYMMDD-HHMM` (local time, {{TIMEZONE}}). Mark urgency honestly: `urgent` | `today` | `this week` | `whenever`. Never edit or delete an item after writing it; if something changes, append a new item that references the old id. Once {{AGENT_NAME}} records an id as delivered, the item may be moved to `## Delivered`; prune delivered items older than 14 days.

## For {{PRINCIPAL_NAME}} ({{AGENT_NAME}} surfaces these)

## For {{AGENT_NAME}} (routing / mirroring)

## Delivered
