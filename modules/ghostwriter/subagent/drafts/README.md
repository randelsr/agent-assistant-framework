# drafts/

One file per draft request: `YYYY-MM-DD-<slug>.md` (date of v1). Revisions update the same file and bump `status`.

## Frontmatter

```yaml
---
type: draft
format: post | blog | thread | memo
target_length: "1500 chars" | "900 words" | "8 posts"
topic: <one line>
status: v1 | v2 | v3 | published | archived
tier: A | B | C
topic_anchor: <corpus slug or concept page>
created: YYYY-MM-DD
last_revised: YYYY-MM-DD
---
```

## Lifecycle

- Ghostwriter writes v1.
- {{PRINCIPAL_NAME}}'s feedback comes through {{AGENT_NAME}}; Ghostwriter updates the same file (v2, v3...).
- Published: {{AGENT_NAME}} saves the final text to `raw/writings/` and submits it to the Librarian; set `status: published`.
- Abandoned: `status: archived` with a one-line note.
