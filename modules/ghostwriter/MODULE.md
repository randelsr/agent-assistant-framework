# Module: ghostwriter

Drafts posts, long-form articles, threads and internal memos in the principal's voice, then stops. It never publishes. Voice is calibrated against `wiki/concepts/voice.md`, a page the principal fills in during setup (registers, signature phrases, anti-patterns, sign-offs, and links to 3 to 5 representative pieces), plus whatever published writing lives in `wiki/writings/`. Every draft is self-graded A/B/C, and a C is returned as a question instead of a draft.

- **Profile fit:** both (work: memos, announcements, thought-leadership posts; personal: blog and social).
- **Inputs it needs:** a filled-in `wiki/concepts/voice.md`; ideally a few published pieces in `wiki/writings/` (submitted through the Librarian) or `raw/writings/`.
- **Tools / MCP:** web search and fetch only. No posting integrations, by design.
- **Thread mode:** no. Subagent only.
- **Schedule:** none. On demand.
- **Install:** copy `subagent/` to `subagents/ghostwriter/` and `agent.md` to `.claude/agents/ghostwriter.md`. Create a stub `wiki/concepts/voice.md` if the template did not.
