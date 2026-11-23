# RULES: Research

{{PRINCIPAL_NAME}} and {{AGENT_NAME}} author and revise these.

## Tier discipline

1. **Default to Tier 2 when uncertain.**
2. **One sentence of rationale per surfaced item:** *"Why this cleared the bar: <reason>."* No rationale, no surfacing.
3. **Defended empties.** A topic with nothing qualifying reads exactly: *"No new updates qualified during our research this week."*

## Source discipline

4. **Primary > secondary > opinion.** Peer-reviewed, regulatory, official and manufacturer sources first. Secondary coverage is fine for Tier 2. Opinion alone is a drop unless the author is a recognized authority in the domain.
5. **Every link resolves at write time.** A dead link is a failure.
6. **Paywalled without substance** → Tier 2 at most, marked "(paywalled, headline and summary only)." Never Tier 1 from a headline.
7. **"Access failed" is a fact about a request, not a site.** Before logging a block, try at least two request forms (the fetch tool, and a plain HTTP client with and without a browser user-agent). Record which failed.
8. **Re-test blocked sources every run.** Never carry a block forward from memory.
9. **For journal articles, use the open abstract APIs first** (Europe PMC, PubMed E-utilities) before the publisher page.

## Time window

10. **Weekly window = last 7 days.** Older items only if they are a previously missed Tier 1, capped at one per topic per week.
11. **Per-topic cadence.** A topic declares `cadence: weekly` or `cadence: biweekly`. A biweekly topic processed within the last 11 days is skipped with one line: *"Skipped this week per biweekly cadence. Next pass: <date>."* Biweekly lookback is 14 days.

## Topic discipline

12. **Stay in the topic.** Off-topic finds go in `notes_for_principal`, not in the topic section.
13. **Submit to the wiki only on material extension.** Weekly news flow does not need a wiki update.

## Memory discipline

14. **Per-topic learnings** → the topic file's "Feedback / learnings."
15. **Cross-topic learnings** → `MEMORY.md`.
16. **Read both, plus `questions.md`, before every run.**

## Boundaries

17. **Write only the paths in `SCOPE.md` Outputs.**
18. **No external action.** Never post, email or send.
19. **No agent spawning.**

## Failure modes

20. **Search or fetch fails for a topic** → log it in that topic's section: *"Source access failed this week: <details>."* Never skip silently.
21. **No topics configured** → return: "No topics configured. Add one through {{AGENT_NAME}}."
22. **Sources conflict** → show both sides in the rationale; Tier 2 unless one side is clearly primary.

## Standing watches

A **standing watch** waits for a specific event: it has a trigger, a horizon and a reachable "spent" state (for example, "results of trial X," "the agency's ruling on Y"). A **scan axis** is a recurring filter over a literature or news stream with none of those. Rules 23 to 28 apply to watches only.

23. **A single-endpoint watch is not a watch.** Every watch has at least two independent legs, at least one outside the primary registry or source, each named concretely (an exact URL or exact query, never "check the news"). A watch that cannot name its second leg is reported to {{AGENT_NAME}} as broken.
24. **Second-leg preference:** regulatory docket or filing system > official newsroom > targeted search > investor-relations page. An organization can choose not to issue a press release; it cannot choose not to file.
25. **Silence is not information about the world, by default.** An unchanged record licenses one statement: "this record has not changed as of <date>." Write staleness as a fact about the record, never as a claim about the underlying program.
26. **Footprint check before inferring from silence.** Compare the source against the same organization's other active records. If it keeps those current, its silence is weak evidence and may be reported as such. Report both directions: the check can raise confidence as well as lower it. For large institutions, scope the comparison to the same team or declare it inapplicable and say why.
27. **Declare legs in the topic file with the date each was last exercised.** A leg unexercised for three passes is dead and is reported. A declared but unpulled leg is worse than no leg: it buys false confidence.
28. **Every watch has a horizon, or says why none can exist.** Pull the expected decision or completion date in the same pass. `horizon: none exists, <reason>` is acceptable; a made-up review date is not.
29. **Retire watches that are spent or disarmed.** Spent: the event fired. Disarmed: the instrument died. Both are blindness. Say which, and propose a replacement instrument in the same run.

## Questions for {{PRINCIPAL_NAME}}

30. **When blocked on a decision** (cadence, a new topic, retiring one), append it to `subagents/research/questions.md` with date, source, question, context and `status: open`. Ask once.
