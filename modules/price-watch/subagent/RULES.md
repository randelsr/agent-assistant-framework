# RULES: Price Watch

## Qualification

1. **The item's rule is the rule.** No "close enough."
2. **Every surfaced item states its trigger:** *"target 500 hit at 465 (7% below target)"*, *"historical low: 465 (previous low 480)"*, *"drop from 500 to 465."*
3. **Empty digest is exactly:** *"No tracked items on sale today."*

## Anti-fake-sale

4. **Track a 7-day list-price baseline per item.** If the list price was raised within 7 days before a discount: *"List was X 7 days ago, raised to Y, then 'discounted' to Z. Real discount from baseline: N%."* Surface only if the real price still clears the rule.
5. **Rotating "sales."** If an item has shown the same "sale" price more than 3 times in 90 days, treat it as the effective list price. Note it in the item's `Feedback / learnings`.
6. **Condition mismatch.** With `condition: new`, a qualifying used or open-box price is noted, not surfaced.
7. **Never recommend relaxing an item's condition, target or rule.** Those change only when {{PRINCIPAL_NAME}} says so.
8. **Compute % off from the observed baseline,** not from an on-page "MSRP" or "was" string that may be inflated.
9. **A holiday banner is not a discount.** Count a sale only when the product page itself shows the reduced price or rate for the tracked item.

## Sources

10. **Every link resolves to the product page** at write time.
11. **Multi-retailer by default,** respecting `preferred_retailers` and `exclude_retailers`. Surface the lowest qualifying price; note the spread if several qualify.
12. **Failures are visible:** *"Source check failed: <reason>."* Never skip silently.
13. **Code-only and member-only prices are not shelf prices.** Note them as context; never count them as qualifying unless the item file says to.

## Item file discipline

14. **Read-only frontmatter.**
15. **Append-only `Price history`,** trimmed to 90 days at write time.
16. **Append-only `Feedback / learnings`.**

## Time

17. **Current prices only.** A sale that ended yesterday is not surfaced.
18. **One daily run per day.** If today's digest exists, a daily run returns: "Today's digest already exists." A single-item check appends to it.

## No external action

19. **No buying, checkout, sign-ups, coupons, cart or wishlist edits, or account interaction.** Read-only lookups.

## Failure modes

20. **Unexpected page structure** → skip with reason under Notes; suggest {{PRINCIPAL_NAME}} re-confirm the URL if it persists.
21. **No price source resolves** → *"Item '<slug>' uncheckable: no source resolved. Suggest archiving or fixing."*
22. **`status: archived`** → skip silently.

## Memory

23. **Cross-item patterns → `MEMORY.md`.** Per-item → the item's `Feedback / learnings`. Read both, plus `questions.md`, every run.

## Questions for {{PRINCIPAL_NAME}}

24. **When blocked** (a target that seems wrong, a dead product, a new-item criterion), append to `questions.md`. Never ask about relaxing condition.
