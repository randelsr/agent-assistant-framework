# Module: price-watch

A daily price checker for a watch list. Each item file carries its own qualification rule (target-hit, historical-low or any-drop) and condition requirement; the agent checks prices across retailers, appends a 90-day price history, and surfaces only items whose rule actually fires. It is built to resist retailer theater: list-price inflation before a "discount" gets flagged with the real discount from baseline, recurring "sale" prices are treated as the effective list, and member-only or code-only prices do not count as shelf prices. An empty day is one line. It never buys anything.

- **Profile fit:** personal (also usable for work procurement watches: hardware, software licenses, travel fares).
- **Inputs it needs:** item files in `items/`, created by the main agent from the template when the principal names a product and a rule.
- **Tools / MCP:** web search and fetch only.
- **Thread mode:** no.
- **Schedule:** daily, early morning in {{TIMEZONE}}. Skip when no item is `active`.
- **Install:** copy `subagent/` to `subagents/price-watch/` and `agent.md` to `.claude/agents/price-watch.md`.
