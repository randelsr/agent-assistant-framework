# Questions for {{PRINCIPAL_NAME}}

{{AGENT_SHORT}}'s open questions that only the principal can answer. Each subagent keeps its own `subagents/<name>/questions.md` in the same shape.

**Rules**

- Add an entry to `## Open` only if the principal must decide it before their next touchpoint, or if it is a cross-day deferral they asked for ("ask me Friday"). Everything else is either researched and decided by the agent, or attached to the next scheduled touchpoint.
- Surface **one question at a time** in the check-in, most blocking first.
- When the principal answers, move the entry to `## Answered` **in the same turn** with the resolution. Never delete; move.
- If a question becomes moot, move it to `## Withdrawn` with the reason.
- Answering a question closes it. Do not spawn follow-ups unless they change what someone does before the next touchpoint.

**Entry format**

```
- [YYYY-MM-DD] <question in one sentence> | why it matters: <one line> | blocking: <mission or "nothing"> | defer-until: <date or "none">
```

## Open

- *(none)*

## Answered

- *(none)*

## Withdrawn

- *(none)*
