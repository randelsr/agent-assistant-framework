# Module: meal-planner

A household chef that proposes a weekly dinner menu, writes complete recipes once the menu is approved, carries every substitution through recipe and list, and produces a consolidated five-category shopping list that must end with an ingredient-by-ingredient audit line ("N ingredients across M recipes checked, 0 missing"). Preferences live in a fill-in `household-profile.md` (who eats, allergies, dislikes, heat tolerance, cuisines, weekly targets, time caps), and it keeps a meal history for a two-week no-repeat rule, a dated pantry list, and a rotation of keeper recipes. A weekly kickoff sends one opener and never nudges.

- **Profile fit:** personal.
- **Inputs it needs:** a filled-in `household-profile.md` (it will ask for the essentials on first run if empty).
- **Tools / MCP:** web search and fetch for technique questions only. Optional: the workspace messaging bridge for message mode.
- **Thread mode:** yes. Has an `outbox.md`; follows `subagents/THREADS.md`.
- **Schedule:** weekly kickoff, e.g. Saturday morning in {{TIMEZONE}}, delivered outside quiet hours.
- **Install:** copy `subagent/` to `subagents/meal-planner/` and `agent.md` to `.claude/agents/meal-planner.md`.
