# Module: pet-care

A veterinary specialist for the animals in the principal's household. It keeps one living record per animal (diagnoses, protocol, labs trend, care flags, items to raise with the vet), runs a light weekly check-in and a monthly deep review, and does deep on-demand research when a diagnosis or treatment question comes up. Everything is tiered from species-specific evidence down to anecdote, care flags come first, and clinical decisions are always framed as questions for the treating vet. It never books, orders or contacts anyone.

- **Profile fit:** personal.
- **Inputs it needs:** at least one animal record (create `animals/<name>.md` from the README template with the principal); vet records dropped in `raw/veterinary/<animal>/` when available.
- **Tools / MCP:** web search and fetch only.
- **Thread mode:** yes. Has an `outbox.md`; follows `subagents/THREADS.md`.
- **Schedule:** weekly check-in (e.g. Saturday afternoon) and monthly review (the 1st), in {{TIMEZONE}}. Skip both while no animal is `active`.
- **Install:** copy `subagent/` to `subagents/pet-care/` and `agent.md` to `.claude/agents/pet-care.md`. Create `raw/veterinary/` if missing.
