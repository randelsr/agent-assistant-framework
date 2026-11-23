# organizations/

Employer, internal teams, customers, vendors, partners. One page per organization (`<slug>.md`). Teams inside the employer can be their own pages when they matter on their own.

**Frontmatter**

```yaml
---
type: organization
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: <active|former|prospect>
relationship: <employer|team|customer|vendor|partner>
since: YYYY-MM-DD
until:            # blank while active
---
```

**Suggested sections:** what they do, the principal's relationship to them, key stakeholders (links), active projects (links), commercial or contractual terms that matter (with Value-Interface tags on any number), history.

**Confidential material.** If a page holds anything non-public (unannounced deals, compensation, internal financials), mark the section `CONFIDENTIAL` and keep figures out of `index.md` rows.

Written only by the Librarian.
