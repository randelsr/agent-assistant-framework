# digests/: the Librarian's run outputs

One file per run: `YYYY-MM-DD.md` (add `-<slug>` for on-demand runs). {{AGENT_NAME}} reads the latest unread digest at session start and surfaces refinement requests, layer-scope violations and restructure proposals.

## Format

```markdown
---
type: librarian-digest
date: YYYY-MM-DD
submissions_processed: N
integrated: N
archived: N
rejected: N
refinement_requested: N
autonomous_fixes: N
deferred_for_review: N
generated_by: librarian
---

# Librarian Digest: YYYY-MM-DD

## Submissions processed (N)

### Integrated (N)
- **<source>**: `<proposed_path>` → `<final_path>`. <notes; why the path changed, if it did>

### Archived (N)
- **<source>**: `<filename>`. <rationale>

### Rejected (N)
- **<source>**: `<filename>`. <rationale>

### Refinement-requested (N)
- **<source>**: `<filename>` needs <specific fix>. Notes appended in `.refinement-requested/`.

## Structural sweep

### Autonomous fixes (N)
- <what was fixed, where>

### Deferred for review (N)
- <what, why it needs a decision>

### Layer-scope violations (N)
- <page, what drifted>

## Lint
<broken links, orphans; or "lint script not present">

## Notes for {{AGENT_NAME}}
<anything to surface>
```

## Quiet week

Still write the file, briefly:

```markdown
# Librarian Digest: YYYY-MM-DD

No submissions this week. Sweep clean. Lint: 0 broken, 0 orphans.
```

All digests are kept. They are the history of how the wiki evolved, alongside `wiki/log.md`.
