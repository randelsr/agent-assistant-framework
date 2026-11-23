# SCOPE: Price Watch

## Domain

Daily price check on tracked items. Surface only the items whose rule fires today. An empty digest is normal.

Items are added, archived and edited through {{PRINCIPAL_NAME}} ↔ {{AGENT_NAME}} conversation. {{AGENT_NAME}} edits the item files.

## Triggers

Invoked by {{AGENT_NAME}} via the Agent tool with `subagent_type: price-watch`:

1. **Daily run** (scheduled, suggested early morning {{TIMEZONE}}). Prompt: *"Run today's price check on all active tracked items."* Every `items/*.md` with `status: active`.
2. **Single-item check.** Prompt: *"Check '<slug>' now."* Same logic, one item.

## Tools

`Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch`. No Agent tool.

## Qualification rules

| Rule | Frontmatter | Fires when |
|---|---|---|
| `target-hit` | `target: <number>` | Current price ≤ target. Most common. |
| `historical-low` | none extra | Current price ≤ the lowest in the item's Price history. |
| `any-drop` | none extra | Current price < the previous observation. |

With `condition: new`, used, refurbished and open-box prices never qualify (note them, do not surface).

## Outputs

| Path | When | What |
|---|---|---|
| `subagents/price-watch/digests/YYYY-MM-DD.md` | Every daily run | Qualified items first; failures noted. Empty: the one line. |
| `items/<slug>.md`, `Price history` | Every run, every active item | `- YYYY-MM-DD: <price> (<retailer>) <condition>`, trimmed to 90 days |
| `items/<slug>.md`, `Feedback / learnings` | An item-specific pattern is learned | `- YYYY-MM-DD: <observation>. *Apply by:* <how>.` |
| `subagents/price-watch/MEMORY.md` | A cross-item pattern | Entry with **Why:** and **How to apply:** |
| `subagents/price-watch/memory/active-work.md` | Run start and end | Operational state |
| `subagents/price-watch/questions.md` | Blocked on {{PRINCIPAL_NAME}} | Open question |

Nothing else. Never edits item frontmatter or other item sections.

## Report back to {{AGENT_NAME}}

```
- digest_path: <path>
- items_checked: N
- qualified_count: N
- source_failures: [<slugs>]
- notes_for_principal: <suspected fake sales, URL changes, items that may need archiving>
```
