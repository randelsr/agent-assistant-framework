# Outbox delivery ledger

Append-only. Written only by {{AGENT_SHORT}} Ops. One line per outbox item relayed to the principal or routed to another agent. Agents read this to know which of their outbox items have been delivered; they never write it.

Format: `- <item id> | <YYYY-MM-DDTHH:MM±HH:MM> | <how: check-in / [URGENT] / routed to <agent>>`

Commit this file alone: `git commit -m "Ops: outbox ledger" -- memory/outbox-delivered.md`

## Delivered
