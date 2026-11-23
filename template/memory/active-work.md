# Active Work Tracker

<!-- {{AGENT_SHORT}} writes here IMMEDIATELY when spawning sessions or starting async work. -->
<!-- Read at every session start and every heartbeat to recover dropped work. -->

**Purpose.** Live, in-flight items only: open asks to the principal, pending decisions, scheduled relays, owed subagent relays, unresolved flags, and standing instructions still in force. Finished history does not live here.

**Format.** One item per entry, a few lines each: what, status, next action or date, and a pointer to full history. Group by section. When an item closes, move its full text to `memory/archive/active-work-YYYY-MM.md` (bucketed by the entry's own date). Never just delete it.

**Budget.** Under 50 KB. The weekly GC (`HEARTBEAT.md`, `memory_gc_weekly`) enforces it losslessly.

*Last GC: YYYY-MM-DD. Money and metrics carry Value-Interface tags.*

---

## 1. Asks pending with the principal

*(Asked, waiting on them. Do not chase unless noted.)*

- *(none)*

## 2. Scheduled relays by date

*(Lines that must go out on a given day. If a line is marked verbatim, send it exactly as quoted.)*

- *(none)*

## 3. In-flight async work

*(Every spawned session, background subagent or long job: what, where, started, what you are waiting on, which files it will write.)*

- *(none)*

## 4. Owed subagent relays and riders

*(Things a subagent must be told on its next run. Mirror any one-shot rider into `HEARTBEAT.md`.)*

- *(none)*

## 5. Standing instructions in force

*(Temporary instructions from the principal that are not permanent enough for `USER.md`, with their expiry.)*

- *(none)*

## 6. Unread digests

*(Digest paths written by subagents and not yet surfaced.)*

- *(none)*

## 7. Sessions

*(Live session ids and cron bookkeeping. Ops reads this to address Admin and to know when to recreate the heartbeat cron.)*

- {{AGENT_SHORT}} Admin session id: `<fill in at setup>`
- {{AGENT_SHORT}} Ops session id: `<fill in at setup>`
- Heartbeat cron created: `YYYY-MM-DDTHH:MM` (recreate after about 6 days)
- Thread agents: *(none)*
