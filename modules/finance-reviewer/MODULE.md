# Module: finance-reviewer

An independent, dialectical peer reviewer for the Finance Analyst's strategic recommendations. Before any allocation pick, tax engineering plan, conviction trade, methodology lock or withdrawal reaches the principal, the main agent (or the analyst itself in thread mode) argues it through with this reviewer over several rounds: steelman, convert labels to falsifiable claims, run the test, quantify the trade-off as a money ratio, sweep any sizing parameter, check it against the principal's ratified investor profile, and concede when the data settles it. The principal only sees the converged joint recommendation, with what was ruled out and the condition under which it would flip.

- **Profile fit:** personal (paired with `finance-analyst`).
- **Inputs it needs:** the Finance Analyst's draft and artifacts; the investor profile in `subagents/finance-analyst/MEMORY.md`.
- **Tools / MCP:** Bash, Read, Glob, Grep, and Write for its own review records. No finance MCP; it reasons over what the analyst pulled.
- **Requires:** `finance-analyst`.
- **Thread mode:** no.
- **Schedule:** none. Dispatched on every strategic recommendation.
- **Install:** copy `subagent/` to `subagents/finance-reviewer/` and `agent.md` to `.claude/agents/finance-reviewer.md`. Add a line to the main agent's `CLAUDE.md` or `MEMORY.md` that strategic finance recommendations always go through this review before relay.
