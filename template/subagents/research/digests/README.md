# digests/: weekly research outputs

One file per weekly run: `YYYY-MM-DD.md`. {{AGENT_NAME}} surfaces the latest unread digest at session start. All digests are kept as a record of what was on the radar and when.

## Format

```markdown
---
type: research-digest
date: YYYY-MM-DD
topics_processed: N
tier_1_count: N
tier_2_count: N
drops_count: N
generated_by: research
---

# Weekly Research Digest: YYYY-MM-DD

## <topic name>

### Tier 1: changes the thesis
- **<title>**: [link](url)
  - <2-3 sentence summary>
  - **Why this cleared the bar:** <one sentence>

### Tier 2: noteworthy datapoint
- **<title>**: [link](url)
  - <1-2 sentence summary>
  - **Why this cleared the bar:** <one sentence>

### Watches
- <watch>: <legs exercised, record state as of date, horizon>

### Notes
- <source failures, unusual signals>

---

## <next topic>

No new updates qualified during our research this week.

---

## Cross-topic notes for {{AGENT_NAME}}
<implications, suggested topic changes, source problems>
```

## Empty week

```markdown
# Weekly Research Digest: YYYY-MM-DD

No new updates qualified during our research this week.
```
