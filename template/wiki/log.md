---
type: log
tags: [log, operations]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Wiki Log

Append-only chronological record of wiki operations. Written by the Librarian. Newest entries at the bottom. Never edit or delete a past entry; if one was wrong, append a correction that references it.

**Entry format**

```
## [YYYY-MM-DD HHMM TZ] <ingest|curate|lint|correction> | <subject>

- Source: <submission filename, raw/ path, or "structural sweep">
- Pages touched: <paths>
- Notes: <what changed and why, one or two lines>
```

---

## [YYYY-MM-DD HHMM TZ] curate | Wiki initialized

- Source: framework template
- Pages touched: `index.md`, `log.md`, `people/principal.md`, folder READMEs
- Notes: Seed structure for profile `{{PROFILE}}`.
