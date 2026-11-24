# Heartbeat

The heartbeat is how the agent runs itself between conversations. A cron fires every five minutes in the Ops session; each fire reads `HEARTBEAT.md` and does whatever is due. This document explains the design; the operative protocol lives in the workspace's `HEARTBEAT.md`.

## One heartbeat, not a cron fleet

**The heartbeat is the single entrypoint for all recurring work.** Weekly subagent runs, the daily check-in, memory GC, inbox triage: each is a row in a dispatch table, not its own cron.

Why: task-specific crons multiply, expire independently, drift, and cannot be audited in one place. A dispatch table is one file you can read top to bottom to know everything the agent will do this week. The only legitimate one-off cron is a sub-day, moment-specific reminder ("ping me in two hours"). Cross-day deferrals ("ask me Friday") live in `memory/questions.md` and resurface in the check-in.

## Cadence

```
0,5,10,15,20,25,30,35,40,45,50,55 * * * *
```

An explicit minute list rather than `*/5`, so fires land on clean boundaries. Created with `CronCreate`, recurring, in the Ops session only.

Five minutes is fast enough that an urgent outbox item reaches the principal within minutes, and slow enough to be cheap when most fires end in `HEARTBEAT_OK`. If replies get slow, **cadence is not the lever:** check the conversation log for API or connection errors first. A run of connection errors means restart the session (or check the network), not re-tune the heartbeat.

## The dispatch table and the missed-fire rule

Each row has a target time, a `lastChecks` key in `memory/heartbeat-state.json`, and a window:

| Window | Start |
|---|---|
| calendar-day | today 00:00 local |
| calendar-week | this Sunday 00:00 local |
| calendar-month | the 1st 00:00 local |

A row fires when:

```
now >= target_time  AND  lastChecks[key] < start_of_current_window
```

and stamps `lastChecks[key] = now` after firing. That rule is **self-correcting**: if the session was busy, asleep or offline at the target time, the next heartbeat after it recovers still satisfies the condition and runs the missed task, exactly once per window. No catch-up logic is needed anywhere else.

Interval rows (for example inbox triage every 15 minutes) use `now - lastChecks[key] >= interval` instead.

The workspace's `HEARTBEAT.md` ships with the core rows in the table and one commented `module:<slug>` row per scheduled module trigger below it. `bin/init_workspace.py` (and `--update-config`, for a module enabled later) moves the rows of every enabled module into the table, so the table always matches what is installed.

Besides the table, every heartbeat also runs two cheap checks: `scripts/login-age.py`, which says when the principal should re-run `/login` before a long-running session's login expires, and, if the messaging bridge is configured, a re-forward of any pass-through item Admin has not acknowledged within 15 minutes.

## Self-healing

Recurring crons created by the tool **auto-expire after 7 days.** A heartbeat that does not maintain itself dies silently a week after setup. So every heartbeat:

1. Runs `CronList`.
2. If the heartbeat cron is missing, recreates it with the exact same prompt.
3. If the cron is older than about 6 days (creation time recorded in `memory/active-work.md`), recreates it proactively.

The heartbeat is its own gardener. Only Ops creates crons; thread sessions and Admin never do.

A SessionStart hook can also check on startup and remind the session to recreate the cron if it is missing, which covers restarts.

## Liveness signals that do not lie

Hooks, not the model, write the liveness fields:

| Field | Written by | Meaning |
|---|---|---|
| `lastHeartbeatFire` | `UserPromptSubmit` hook matching the heartbeat prompt | A heartbeat prompt arrived |
| `lastOpsTurnOk` | `Stop` hook in Ops | An Ops turn actually completed |
| `lastSessionStart` | `SessionStart` hook | A session started |
| `pendingRecovery` | Heartbeat hook | A gap was detected |

Two signals are needed because a cron can keep firing while every turn fails (API errors, an expired login). `lastHeartbeatFire` alone would look healthy through a day-long outage. The gap check fires when **either** the previous fire was more than 15 minutes ago **or** the last completed turn was more than 30 minutes ago.

Admin runs a prompt hook on each of the principal's messages that compares those fields against thresholds. If Ops is stale, Admin tells the principal in one line and restarts Ops. A process cannot detect its own death; this is detection from outside.

## Outage recovery

Outages are expected. When `pendingRecovery` is present:

- **Burst:** when the network returns, queued polls arrive together. Do the full recovery once; answer the rest `HEARTBEAT_OK`.
- **Missed dispatches** catch up automatically through the missed-fire rule. A late check-in carries one line: "late: outage HH:MM-HH:MM."
- **Inbound channels:** messages that arrived during the outage may never be re-delivered by a channel plugin, so tell each channel session to run its own catch-up.
- **Failed hand-offs** to Admin are resent.
- Journal one line, clear `pendingRecovery`.
- Don't alert the principal about the outage itself unless something time-sensitive was missed.

## The daily check-in

The one proactive message the principal can count on. **Unconditional and daily,** weekends included, even if it says "All clear."

It has three independent firing paths, because it is the thing whose absence the principal notices first:

1. The Ops dispatch row.
2. A desktop scheduled task at a backstop time that messages Admin only if today's check-in is unstamped.
3. The **first-touch-of-day rule:** on the first turn of a new day in any session, if the check-in has not gone out, send it before anything else. Deep work on something else is exactly how a check-in gets skipped for days.

Ops builds it from missions (stale ones get **continue / hold / kill?**), one open question, unread digests, outbox items, and the next 24-48 hours of calendar. One message, ranked, one screen.

## Speak vs stay quiet

Ops speaks (through Admin) only for:

- `[CHECKIN]`: the morning check-in.
- `[URGENT]`: a deadline within 5 days, a red flag, anything that cannot wait.
- `[FYI]`: everything else, batched into the next check-in unless time-sensitive.

Ops stays quiet (`HEARTBEAT_OK`) when nothing is new, during quiet hours, on weekends for non-urgent work, and whenever the honest answer is "nothing needs the principal." The principal never sees heartbeat mechanics.

Weekend rule: the check-in still goes out; work items are present but soft. A weekend rule that suppresses the check-in turns into a mute button.

## Riders

Weekly dispatch prompts carry **standing riders** (the subagent runs its own memory GC; it adds an Open question only if the principal must decide before their next touchpoint). One-time instructions for a subagent are **one-shot riders**: written into `HEARTBEAT.md` naming the dispatch they ride on, appended verbatim to that dispatch, then struck through with the delivery date. A TODO that is not attached to a firing mechanism is a note about intentions, not a fix.

## Memory GC

A weekly row keeps memory lean without losing anything:

- Entries in `active-work.md`, `MEMORY.md` and `missions.md` are sorted into live, finished and stale (14+ days without movement).
- Durable facts about the principal go to the Librarian as submissions.
- Finished and stale history moves **verbatim** to `memory/archive/<file>-YYYY-MM.md`.
- Live items are compacted with an archive pointer.
- Budgets: `active-work.md` under 50 KB, each `MEMORY.md` under 40 KB.
- **Lossless gate:** a script verifies every removed line exists in the archive before the trimmed file is written.

Subagents run the same GC on their own files via the standing rider.

## Retiring a row

Removing a dispatch, a watch or a state key is not done until every reference to it is grepped and removed in the same change. A stale description of a retired watch, 30 lines above its retirement note, will be believed by the next reader.
