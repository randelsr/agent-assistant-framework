# animals/

One record per animal: `<go-by-name>.md`, lowercase and hyphenated. The state of truth for that animal.

## Frontmatter

```yaml
---
type: animal
name: <full name>
go_by: <short name>
species: dog | cat | other
breed: <breed or unknown>
sex: M | F | M-neutered | F-spayed | unknown
dob: YYYY-MM-DD or YYYY-MM (estimated)
weight: <current; history in body>
status: active | hospice | deceased | rehomed
diagnosed_conditions: []
care_flags: []
last_check: YYYY-MM-DD
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## Body sections

1. Identification
2. Diagnoses: active and historical, with dates and staging
3. Suspected etiology: working hypothesis, evidence, what would sharpen it
4. Prognosis: vet-stated and literature range
5. Current protocol: medications (drug, dose, frequency, start date), diet, supplements, monitoring schedule
6. Care flags, each with its rationale
7. Labs trend table
8. Open data gaps
9. Tier-A items to raise with the vet, with status (proposed, discussed, declined, adopted)
10. Quality-of-life notes
11. Weight history

## Lifecycle

Created when an animal comes into scope. Updated after every check-in, lab review or treatment change. `hospice` when care becomes comfort-focused. `deceased` when the animal dies; the record is kept, never deleted.

Source records (vet PDFs, lab images) stay in `raw/veterinary/<animal>/`.
