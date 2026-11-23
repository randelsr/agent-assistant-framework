# Value-Interface Schema

**Never pass a loose value.** Every load-bearing number carries the context that makes it unambiguous: across the main agent, every subagent, digests, scripts, wiki pages and messages to the principal.

## Why this exists

In a multi-agent system a number is copied many times: from a live source into a snapshot, from a snapshot into a digest, from a digest into a relay, from a relay into a recommendation. Each hop strips a little context. The same three bugs recur:

1. **A slice cited as a total.** "The account is at 80k" when 80k was one asset class inside a 110k account. "The team has 12 open bugs" when 12 was the P1 slice. This is the single most common number bug in practice, and it repeats because the slice and the total look identical once the label is gone.
2. **An estimate promoted to fact.** A modeled value, a rule of thumb, or something the principal said in passing gets cited later as if it were measured.
3. **A stale snapshot cited as current.** A figure that was true on Monday gets re-cited on Thursday as "the" number.

A bare number has no defense against any of these. A tagged value does: the tag travels with the number and the next reader can see what it is.

## The record

| Field | Meaning | Kills |
|---|---|---|
| `value` | The number | |
| `unit` | `USD`, `pct`, `count`, `hours`, `days`, `shares`, ... | Unit confusion |
| `scope` | Aggregation level: `org_total`, `team_total`, `person_total`, `household_total`, `account_total`, `<dimension>_slice`, `single_item` | Slice-cited-as-total |
| `entity` | Who and what it is about, e.g. `{person, account}`, `{team, metric}`, `{project, milestone}` | Wrong entity |
| `breakdown` | The slice dimension(s) if a slice (e.g. `asset_type=US equity`, `priority=P1`); **`null` for a true total** | Ambiguous slices |
| `as_of` | Source sync time or computed-at, ISO 8601 with offset | Staleness |
| `source` | `live` (pulled from the system of record now), `snapshot` (a stored pull), `computed` (a committed script over tagged inputs), `principal_stated`, `estimate`, `document` | Estimate cited as fact |
| `price_basis` | (money only, optional) `market`, `manual`, `mixed` | Hand-entered values that silently go stale |

### JSON form (snapshots and scripts)

```json
{
  "value": 48210.00,
  "unit": "USD",
  "scope": "account_total",
  "entity": {"person": "Alex", "account": "Brokerage A"},
  "breakdown": null,
  "as_of": "2030-01-15T14:30:00Z",
  "source": "live",
  "price_basis": "market"
}
```

```json
{
  "value": 31900.00,
  "unit": "USD",
  "scope": "account_x_assettype_slice",
  "entity": {"person": "Alex", "account": "Brokerage A"},
  "breakdown": {"asset_type": "US equity"},
  "as_of": "2030-01-15T14:30:00Z",
  "source": "live",
  "price_basis": "market"
}
```

```json
{
  "value": 42,
  "unit": "count",
  "scope": "team_total",
  "entity": {"team": "Platform", "metric": "open tickets"},
  "breakdown": null,
  "as_of": "2030-01-15T09:00:00Z",
  "source": "live"
}
```

(All values above are fictional.)

### Prose form (digests, messages)

The tag travels inline. A load-bearing number never appears naked in a digest, recommendation or message.

- Total: `$48,210.00 [Alex·Brokerage A·account_total·live·2030-01-15T14:30Z]`
- Slice: `$31,900 [Alex·Brokerage A·slice:US-equity·live·2030-01-15T14:30Z]`
- Statement: `$5,000 [Alex·Checking·transfer·principal_stated·2030-01-12]`
- Estimate: `~$1,200/yr [generic·vendor quote·annual_cost·estimate·2030-01-10]`
- Non-money: `42 open tickets [Platform·team_total·live·2030-01-15T09:00Z]`

Use judgment on what is load-bearing. A number the principal will act on, compare, or repeat to someone else is load-bearing. A page count in a reading list is not.

## Hard rules

1. **No bare number** leaves a tool result, enters a digest or recommendation, or goes to the principal without scope, entity, `as_of` and source. When in doubt, over-annotate.
2. **Totals are computed from the live source** (sum the items for that entity) and labeled as totals. A per-dimension figure is a slice with `breakdown` set, and is **never** relabeled a total. Do not lift an aggregate out of a report organized along a different axis.
3. **`as_of` older than 48 hours, or source unreachable: flag stale, re-pull before relying.** A dated snapshot keeps its date: "as of YYYY-MM-DD, unverified since."
4. **Provenance is sticky.** `estimate`, `principal_stated` and `document` values may not be silently promoted to `live`. On conflict, show both and resolve toward the measurement.
5. **When the principal challenges a number, diagnose from the live source.** Do not reach for the convenient explanation ("it probably drifted").
6. **Arithmetic is scripted.** Any value computed from other values comes from a committed script with inputs as named constants and intermediate values printed. The model never does the math in its head, including "simple" math.

## The relay gate

Before the main agent relays any number a subagent produced:

1. **Script trace:** it appears in the printed output of a committed script.
2. **Cross-script agreement:** if two scripts carry it, they agree; downstream scripts import the canonical one rather than re-deriving.
3. **Official source** for any legal or regulatory limit, threshold or cap, cited inline.
4. **Magnitude sanity:** if it feels off, re-run the script yourself.
5. **Cross-pass continuity:** if it changed since the last pass, a real input change explains it.
6. **Direction check:** one sentence of causality ("X up, Y down, so Z moves this way").
7. **Gate the message, not just the script:** re-sum the rows you actually typed.

## Canonical snapshot pattern

For any domain with a system of record (a finance tracker, an issue tracker, a CRM), the owning subagent maintains a local snapshot (for example `subagents/<module>/snapshot.json`) stored entirely in this schema and regenerated on every pull. The system of record stays authoritative; the snapshot is the labeled local reference every analysis reads from and the reconciliation point when two numbers disagree.

## Module notes

- **Finance modules** add `price_basis`, compute account totals by summing live holdings per account, never quote a household-wide net figure unless the principal asks for one, and attach a "consult a licensed professional" caveat to tax positions.
- **Work-metric modules** (delivery, pipeline, headcount) use `org_total` / `team_total` / `person_total` scopes and treat dashboard tiles as slices until proven otherwise.
- **Health and pet modules** tag lab values with the lab's own reference range and date; a trend is computed by script across tagged points, never eyeballed.
