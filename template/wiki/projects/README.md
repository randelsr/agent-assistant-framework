# projects/

Bounded efforts with a deliverable and an end. If it will never be "done," it belongs in `initiatives/` instead.

**Frontmatter**

```yaml
---
type: project
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: <active|paused|done|cancelled>
phase: <discovery|planning|build|launch|wrap-up>
due: YYYY-MM-DD
owner: <stakeholder link or "principal">
priority: <1-N>
---
```

**Suggested sections:** goal and definition of done, stakeholders, timeline and milestones, decisions log (dated, with who decided), risks, open questions, links to raw sources.

When a project finishes, set `status: done`, add an outcome section, and leave it here; move it to `archive/` only when it stops being useful context.

Written only by the Librarian.
