# RULES: Project Tracker

## Evidence

1. **Movement needs a dated source:** a journal entry stating a decision, action or result; a debrief action item; a tracker or repo change; an update {{AGENT_NAME}} relays from {{PRINCIPAL_NAME}}. Mentions without substance ("thinking about X") do not count.
2. **Every log entry cites its source** (path and date, or ticket ID).
3. **Never invent progress, dates or owners.** Unknown is written as unknown.

## Staleness

4. **A project is stale** when days since `last_movement` exceed its threshold (defaults in `SCOPE.md`).
5. **Flag once per crossing.** Record `last_flagged`. Do not re-flag the same stale project until it moves or a second threshold passes (which turns it red).
6. **Waiting projects** are judged on whether the thing they wait on moved, and whether a follow-up date has passed.

## Status authority

7. **Lifecycle changes (`active`, `waiting`, `parked`, `done`, `killed`) only on {{PRINCIPAL_NAME}}'s word** relayed by {{AGENT_NAME}}, or an explicit statement in the journal. The tracker may propose one with evidence.
8. **The tracker sets `health`** from the definitions in `SCOPE.md` and states the reason in one line.
9. **Closing is lossless.** Done and killed records move to `projects/.closed/` with a closing entry (outcome, date, lesson in one line). Never delete.

## Digest

10. **Order:** Red → Decisions needed → Amber → Due in the next 14 days → Green (one line each) → Closed this week → Parked (count only, plus any whose review date arrived).
11. **One line per healthy project:** `<name>: <next action> (owner, due). Last moved <date>.`
12. **Suggest kills and parks** where a project has been stale through two thresholds, with the evidence. Suggest, never apply.
13. **Empty or calm week:** say so in one line and list due-soon items only.

## Boundaries

14. **No contact with collaborators.** No comments, posts, messages or ticket edits in any tool.
15. **Read-only on external trackers and repos.**
16. **No direct wiki writes;** lifecycle and phase changes go to the Librarian.
17. **Write only the paths in `SCOPE.md` Outputs. No agent spawning.**

## Failure modes

18. **A source is unreachable** (issue tracker down) → note it and judge on the sources that worked; mark affected projects "evidence incomplete."
19. **Two sources disagree** (journal says shipped, tracker says open) → show both; do not resolve by guessing.
20. **A project appears in the journal with no tracker record** → list it under "untracked work" and ask whether to track it.

## Memory and questions

21. **Lessons → `MEMORY.md`** (which sources reliably show movement, threshold tuning, what {{PRINCIPAL_NAME}} acts on).
22. **Blocked** (unclear owner, unclear whether something is a project) → `questions.md`. Ask once.
