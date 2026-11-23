# items/: tracked item configs

One file per tracked item. Price Watch reads every file with `status: active` each day.

## Adding an item

Through conversation: {{PRINCIPAL_NAME}} describes the product and the rule ("standing desk, model X, under 500 new"); {{AGENT_NAME}} creates the file from the template; the next daily run picks it up.

## Template

```markdown
---
type: tracked-item
name: "<product description>"
slug: <lowercase-hyphenated, matches filename>
status: active | archived
qualification: target-hit | historical-low | any-drop
target: <number, only for target-hit>
currency: USD
condition: new | used | open-box | any
preferred_retailers: []
exclude_retailers: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
---

# <Product name>

## What this is
<1-2 sentences: maker, model, key spec, why it is wanted.>

## Qualification
<The rule in plain words, matching the frontmatter.>

## Source notes
<Preferred URL, SKU or model number for disambiguation, known retailer quirks.>

## Price history
- YYYY-MM-DD: <price> (<retailer>) <condition>

## Feedback / learnings
- YYYY-MM-DD: <observation>. *Apply by:* <how>.
```

## Pausing or retiring

`status: archived` stops checks and keeps the file. Moving it to `.archived/` retires it fully. {{AGENT_NAME}} does both.
