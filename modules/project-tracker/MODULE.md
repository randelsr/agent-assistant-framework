# Module: project-tracker

Keeps a working record for each of the principal's projects and initiatives (lifecycle, health, owner, next action, due date, and the date of the last real movement, always backed by a dated source) and watches for silence. A light daily stale scan returns only projects that newly crossed their threshold; a weekly digest leads with what is red and what needs the principal's decision, keeps healthy projects to one line each, and suggests (never applies) kills and parks for work that has been stale twice. It reads the journal, the wiki's initiative pages, the main agent's missions file, meeting debriefs and, optionally, a read-only issue tracker or repo. Lifecycle changes happen only on the principal's word, and initiative-page updates go through the Librarian.

- **Profile fit:** work (also fine for personal projects).
- **Inputs it needs:** nothing up front; projects are added with "Track '<project>'". A daily journal in `raw/journal/` makes movement detection much better.
- **Tools / MCP:** none required. Optional read-only issue-tracker or repository MCP, added to `agent.md` `tools:`.
- **Pairs well with:** `meeting-prep` (debrief action items feed the log).
- **Thread mode:** no.
- **Schedule:** weekly status (e.g. Friday afternoon) and a daily stale scan, in {{TIMEZONE}}. The scan can run from the heartbeat instead of its own schedule.
- **Install:** copy `subagent/` to `subagents/project-tracker/` and `agent.md` to `.claude/agents/project-tracker.md`.
