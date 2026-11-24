# raw/: Immutable Sources

The source-of-truth layer. Agents **read** from here and **never modify** what is here. New files may be added; existing files are not edited, renamed or deleted. If a source was wrong, the correction lives in the wiki with a pointer back to the original.

**Why immutable:** every claim in the wiki and every number in a digest should trace back to something here. If sources can change, nothing can be audited.

## Layout

| Path | What | Written by |
|------|------|------------|
| `journal/YYYY-MM-DD.md` | Daily journal: append-only chronological notes of events, decisions, running context. The one file in `raw/` that grows during the day (append only, never rewrite earlier lines). | {{AGENT_SHORT}} only |
| `docs/` | Documents the principal shares: specs, decks, contracts, policies, offer letters. Keep original filenames plus a date prefix. | {{AGENT_SHORT}} |
| `meetings/YYYY-MM-DD-<slug>.md` | Meeting notes and transcripts. | {{AGENT_SHORT}} |
| `voice/YYYY-MM-DD-<slug>.{m4a,txt,vtt}` | Voice memos and recordings with local machine transcripts. The audio is the source; transcripts are lossy (no speaker labels, garbled names). Re-listen via the `.vtt` timestamps before quoting anything load-bearing. | {{AGENT_SHORT}} |
| `writings/` | Verbatim originals of pieces the principal has published (the Ghostwriter's deeper voice samples). One page each in `wiki/writings/`. | {{AGENT_SHORT}} |
| `<module>/` | Module-specific sources, for example `finance/` (statements, plan documents), `medical/` (records, labs), `veterinary/<animal>/` (vet records). These hold PII; mark them CONFIDENTIAL and consider gitignoring them. Extractions live in the owning subagent's folder or the wiki, never back here. | {{AGENT_SHORT}} |

## Journal entry format

```
# YYYY-MM-DD

- HH:MM <session> <what happened / what was decided / what was learned>
```

Example: `- 14:05 {{AGENT_SHORT}} Admin: principal moved the launch review to Thursday; mission row updated.`

## Privacy

- `raw/` may contain personal and confidential material. Decide per folder whether it is committed or gitignored, and record the decision in this README.
- Never paste raw content into a public artifact, a web request or a third-party tool without the principal's explicit go.
- Extractions that leave `raw/` (into the wiki or a subagent's records) strip identifiers that are not needed for the purpose.
