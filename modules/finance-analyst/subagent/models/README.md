# models/

Reusable analysis models and the scripts that run them. Each model file records method, parameters and a change log so later runs reuse it instead of re-deriving.

Typical models: retirement projection, rebalancing logic, tax-loss-harvest scan, concentration thresholds, cashflow forecast.

## Template

```markdown
---
type: model
slug: <slug>
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active | parked | superseded
script: models/<slug>.py   # if any
---

# <Model name>

## Purpose
## Method
## Parameters
## Inputs required
## Outputs

## Change log
### YYYY-MM-DD: <change>
<what, why, effect>
```

A locked model (one {{PRINCIPAL_NAME}} ratified) changes only with peer review and {{PRINCIPAL_NAME}}'s go-ahead.
