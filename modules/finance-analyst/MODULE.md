# Module: finance-analyst

A read-only financial analyst for the accounts the principal puts in scope: tax-relevance flagging, cashflow and reserve analysis, allocation drift and rebalancing suggestions, expense audits and income review, plus a weekly digest. Every recommendation is rated Conviction × Magnitude, every number carries Value-Interface Schema tags (scope, entity, as-of, source) so a slice is never cited as a total, money moves are always confirmation-gated, and tax positions carry a CPA caveat. Strategic recommendations pass the `finance-reviewer` module before they reach the principal. It ships with an empty "principal-ratified rules" section and an investor-profile section to fill in; it carries no investing framework of its own.

- **Profile fit:** personal (also works for a small-business owner's books, if the data source covers them).
- **Inputs it needs:** a read-only finance data MCP (accounts, transactions, budgets, holdings, allocation, income); optionally `wiki/concepts/investment-thesis.md` and a filled-in investor profile in `MEMORY.md` section A.
- **Tools / MCP:** the read-only finance MCP's tool names must be added to `agent.md` `tools:` at install. No trading or money-movement tools, ever.
- **Requires:** `finance-reviewer` (install both together).
- **Thread mode:** yes. Has an `outbox.md`; follows `subagents/THREADS.md`.
- **Schedule:** weekly digest, e.g. Sunday evening in {{TIMEZONE}}. On demand otherwise.
- **Install:** copy `subagent/` to `subagents/finance-analyst/` and `agent.md` to `.claude/agents/finance-analyst.md`.
