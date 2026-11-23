# recommendations/

One file per actionable recommendation rated H×H, H×M or M×H: `YYYY-MM-DD-<slug>.md`. Closes the loop on what was advised, what {{PRINCIPAL_NAME}} decided, and what happened.

## Template

```markdown
---
type: recommendation
slug: <slug>
created: YYYY-MM-DD
conviction: H | M | L
magnitude: H | M | L
status: open | executed | dismissed | superseded
peer_review: pending | ratified | revised | withdrawn | diagnostic-first
related_position: <slug or null>
related_digest: digests/<file>.md
---

# <Headline>

## The recommendation
<one paragraph: the action>

## Rationale
<data, method, why this rating>

## Risk / caveats
<what could go wrong; tax note; concentration; leverage; CPA caveat if tax-relevant>

## Sensitivity envelope
<under what condition this flips>

## Status updates
*(append-only)*

### YYYY-MM-DD: <change>
- Status: open → executed | dismissed | superseded
- Principal note:
- Outcome vs prediction:
```
