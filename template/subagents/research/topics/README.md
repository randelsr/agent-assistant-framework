# topics/: one config file per research topic

Research reads every file here (except this README and `.retired/`) at the start of each weekly run.

## Adding a topic

Through conversation: {{PRINCIPAL_NAME}} describes the topic, {{AGENT_NAME}} creates the file from the template below, then dispatches a baseline run.

## Template

```markdown
---
type: research-topic
name: <slug, matches filename>
status: active | parked
cadence: weekly | biweekly
baseline_complete: false
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
---

# <Topic name>

## Description
<1-2 sentences: what this covers and why {{PRINCIPAL_NAME}} cares.>

## Sources
- Primary: <databases, regulators, official sites, filings>
- Secondary: <quality outlets>
- Communities: <forums, podcasts, newsletters>

## Tier criteria (overrides)
- Tier 1 for this topic: <e.g. "any peer-reviewed study with a human sample over 50">
- Tier 2 for this topic: <calibration>
- Always drop: <sources>

## Standing watches
*(Only for event watches; see RULES 23-29.)*
- **<watch name>**: trigger <event>; horizon <date or "none exists, reason">
  - Leg 1: <exact URL or query>. Last exercised: YYYY-MM-DD
  - Leg 2: <exact URL or query>. Last exercised: YYYY-MM-DD

## Wiki page
`wiki/topics/<name>.md`, updated only through Librarian submissions.

## Feedback / learnings
- **YYYY-MM-DD**: <observation>. *Apply by:* <how this changes future runs>.
```

## Naming

Lowercase hyphenated slug matching the wiki page name.

## Pausing or retiring

`status: parked` pauses surfacing. Retiring moves the file to `.retired/` (see SCOPE). {{AGENT_NAME}} does both.
