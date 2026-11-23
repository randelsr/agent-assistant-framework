# Module: meeting-prep

Reads the principal's calendar each morning and writes a short, sourced brief for every meeting that deserves one: why the meeting exists, who matters in the room, what is open in both directions, and up to three concrete objectives. Depth scales with stakes (full, standard, a single line, or skip). It draws on the wiki's people, organization and initiative pages, recent journal entries, earlier briefs with the same people, and public professional background on outside attendees. After a meeting it turns the principal's notes into decisions, action items and Librarian submissions, so the wiki's stakeholder pages get richer over time.

- **Profile fit:** work.
- **Inputs it needs:** a read-only calendar integration; a populated `wiki/people/` helps a lot (it will propose pages for new people via the Librarian).
- **Tools / MCP:** a read-only calendar MCP or skill (tool names added to `agent.md` `tools:` at install); optional read-only mail search; web search and fetch.
- **Pairs well with:** `project-tracker` (debrief action items), `inbox-triage`.
- **Thread mode:** no.
- **Schedule:** daily, early morning in {{TIMEZONE}} before the first meeting; weekdays only is a sensible default.
- **Install:** copy `subagent/` to `subagents/meeting-prep/` and `agent.md` to `.claude/agents/meeting-prep.md`.
