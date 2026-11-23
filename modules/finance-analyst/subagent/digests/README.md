# digests/

One file per run: `YYYY-MM-DD-<task-slug>.md`. The weekly run uses `weekly-pulse`. {{AGENT_NAME}} surfaces new digests at the next greeting.

## Shape

- **Frontmatter:** `type: digest`, `subtype` (weekly-pulse, on-demand-query, model-build...), `task`, `created`, `data_freshness` (source sync timestamp).
- **Headline:** one paragraph, bottom line first.
- **Recommendations:** H×H first, then by magnitude. Inline rating on each. Source on every claim. Every number tagged per the Value-Interface Schema.
- **Data references:** which queries and external sources were used.
- **Risk callouts:** concentration, leverage, staleness.
- **Notes for {{PRINCIPAL_NAME}}.**
- **Open questions** (also appended to `questions.md`).

Empty run: *"No actionable signals this run."*
