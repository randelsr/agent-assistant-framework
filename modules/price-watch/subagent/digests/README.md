# digests/

One file per daily run: `YYYY-MM-DD.md`. Kept indefinitely to spot which items see real sales and which see theater.

## Format

```markdown
---
type: price-digest
date: YYYY-MM-DD
items_checked: N
qualified_count: N
source_failures: N
generated_by: price-watch
---

# Daily Price Digest: YYYY-MM-DD

## Qualified

### <item name>
- **Current price:** <price> (<retailer>, <condition>)
- **Trigger:** <target hit / historical low / drop, with numbers>
- **% off baseline:** <N%>
- **Link:** <url>
- **Inflation flag:** (if applicable) <list was X, raised to Y, "discounted" to Z; real discount N%>

## Source-check failures
- **<slug>:** <reason>

## Notes for {{PRINCIPAL_NAME}}
- <patterns, URL changes, archive candidates>
```

## Empty day

```markdown
# Daily Price Digest: YYYY-MM-DD

No tracked items on sale today.
```
