# Module: health-advisor

A medical, physiology and fitness advisor with an integrative but strictly evidence-tiered posture. It interprets records, labs and imaging; turns source documents in `raw/medical/` into a de-identified `wiki/health/` record (through Librarian submissions, one page each); programs training and runs a weekly fitness check once training data is flowing; and runs a monthly screening review against `wiki/health/screenings.md`. Every recommendation carries an evidence tier, anything needing a clinician is returned as an explicit care flag, and every clinical on-demand run leaves a working-record digest. It is not the treating clinician and never books, buys or messages anyone.

- **Profile fit:** personal.
- **Inputs it needs:** source documents in `raw/medical/` (portal exports, lab PDFs, imaging reports); optionally a training-data export for the weekly check; a `wiki/health/screenings.md` page (it can propose the first version).
- **Tools / MCP:** web search and fetch for literature. Optionally a read-only wearable or training-data MCP, added to `agent.md` `tools:`.
- **Thread mode:** yes. Has an `outbox.md`; follows `subagents/THREADS.md`.
- **Schedule:** weekly fitness check (e.g. Sunday afternoon) and monthly screening review (the 1st), in {{TIMEZONE}}.
- **Install:** copy `subagent/` to `subagents/health-advisor/` and `agent.md` to `.claude/agents/health-advisor.md`. Create `raw/medical/` if missing.
