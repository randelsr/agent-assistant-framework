# SCOPE: Research's Contract with {{AGENT_NAME}}

## Domain

Research on a configured set of topics. One file per topic in `subagents/research/topics/<name>.md`. Topics are added and removed through {{PRINCIPAL_NAME}} ↔ {{AGENT_NAME}} conversation; {{AGENT_NAME}} edits the topic files.

## Triggers

Invoked by {{AGENT_NAME}} via the Agent tool with `subagent_type: research`:

1. **Weekly digest** (scheduled, suggested Sunday {{TIMEZONE}}). Prompt: *"Run weekly digest for all configured topics."* Iterate every topic file except `README.md` and anything in `topics/.retired/`.
2. **Baseline a new topic** (on demand). Prompt: *"Baseline '<topic>' for the wiki."* One deep pass producing a state-of-the-art page, submitted to the Librarian. Set `baseline_complete: true` in the topic file afterwards.

Research does not self-trigger.

### Retiring a topic

{{AGENT_NAME}} moves the file to `topics/.retired/<name>.md` and prepends a block with the date, the instruction and the topic's state at retirement.

- Research never processes `.retired/`.
- Retired topics are kept. Their source map and learnings are the expensive part.
- Retirement does not touch the wiki page. It stops updates; it does not erase what was learned.
- Reinstating: move the file back, set `status: active`, remove the block, and re-exercise every declared watch leg (their last-pulled dates will be stale).

## Tools

`Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch`. No Agent tool.

## Tier framework

| Tier | Definition | Example |
|---|---|---|
| **Tier 1** | Changes the thesis. Materially shifts how {{PRINCIPAL_NAME}} would think or act in this domain. | New peer-reviewed result; a regulatory change; a major vendor announcement that re-prices a market. |
| **Tier 2** | Noteworthy datapoint. Worth knowing, does not shift the thesis. | Credible coverage of a secondary development; a product update; an emerging community discussion. |
| **Drop** | Blogspam, recycled news, low credibility, already covered. | Aggregator rewrites; opinion without sources; rumor. |

Feedback on tier calls is appended by {{AGENT_NAME}} to the topic's "Feedback / learnings" section (per-topic) or to `MEMORY.md` (cross-topic). Research reads both every run.

## Outputs

| Path | When | What |
|---|---|---|
| `subagents/research/digests/YYYY-MM-DD.md` | Every weekly run | Tier 1 first, then Tier 2, one rationale line each. Empty topics get the defended-empty line. |
| `subagents/librarian/submissions/research-YYYY-MM-DD-<slug>.md` | A Tier 1 or 2 item materially extends a topic, or a baseline is done | Proposed `wiki/topics/<topic>.md` content. Research never writes `wiki/` directly. |
| `subagents/research/topics/<name>.md`, "Feedback / learnings" and watch-leg dates only | A per-topic pattern is learned or a leg is exercised | Dated entry |
| `subagents/research/MEMORY.md` | A cross-topic lesson | Entry with **Why:** and **How to apply:** |
| `subagents/research/memory/active-work.md` | Run start and end | Operational state |
| `subagents/research/questions.md` | Blocked on {{PRINCIPAL_NAME}} | Open question |

Nothing else.

### Refinement loop

If the Librarian refinement-requests a submission, {{AGENT_NAME}} relays the notes. Research submits a corrected new file with the same `proposed_path`.

## Report back to {{AGENT_NAME}}

```
- digest_path: <path>
- topics_processed: N
- tier_1_count: N
- tier_2_count: N
- drops_count: N
- submissions: [<librarian submission paths>]
- dead_or_disarmed_watches: [<topic: leg, reason>]
- notes_for_principal: <cross-domain implications, source problems, suggested topic changes>
```

{{AGENT_NAME}} records "Unread digest: <path>" in `memory/active-work.md` and surfaces it at the next greeting.

## Handoff to {{PRINCIPAL_NAME}}

Always through {{AGENT_NAME}}.
