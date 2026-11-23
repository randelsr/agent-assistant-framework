# digests/

Working records. Kept indefinitely for trend analysis and history.

## Naming

- Weekly fitness check: `fitness-YYYY-MM-DD.md`
- Monthly screening review: `health-YYYY-MM-DD.md`
- On-demand clinical run: `health-YYYY-MM-DD-<slug>.md` (one file per episode, updated in place across passes)

## Weekly fitness digest

```markdown
---
type: fitness-digest
date: YYYY-MM-DD
sessions_logged: N
recovery_signal: green | amber | red
generated_by: health-advisor
---

# Weekly Fitness Check: YYYY-MM-DD

## Week in review
- Sessions: N / target
- Volume:
- Deviations from program:
- Recovery signals: (HRV, sleep, RPE if available)

## Observations

## Next week
- Priority:
- Sessions:
- Recovery focus:
- Modality additions (with tier):

## Care flags

## Sources cited
```

## Monthly screening digest

Sections: recently completed, due now, overdue (each with a care flag), due in the next 30 days, changes proposed to `wiki/health/screenings.md` (submitted via the Librarian), sources.

## On-demand clinical digest

Sections: question, relevant history (pointers), findings with tiers, differential or interpretation, disposition, care flags, what is still unresolved, sources. Append a dated "Pass N" section on each follow-up.
