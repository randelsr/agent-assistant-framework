# positions/

One file per asset the Finance Analyst materially analyzes: `<slug>.md`. History accumulates across runs so trends are visible, not just snapshots.

## Template

```markdown
---
type: position
slug: <slug>
asset_class: equity | fund | crypto | fixed-income | real-estate | private | cash | other
account: <account label from MEMORY C>
status: active | exited | watching
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# <Asset name>

## Overview
- Account: <label>
- Cost basis source: <how determined>
- Strategic rationale: <why it is held>

## Current snapshot
*(refreshed each analysis; every value tagged)*
- As of:
- Value:
- Cost basis:
- Unrealized P&L:
- Share of portfolio:

## Analysis log
*(append-only, dated)*

### YYYY-MM-DD: <subtitle>
- Take:
- Recommendations: [C×M] <action>. <rationale, source>
- Risk callouts:

## Feedback / learnings
- YYYY-MM-DD: <observation>. *Apply by:* <how>.
```
