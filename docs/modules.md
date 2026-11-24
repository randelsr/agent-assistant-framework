# Modules

A module is one subagent: a scoped agent with its own identity, rules, memory and output folders, plus the Claude Code wiring that bootstraps it. Two are core and always installed. The rest are optional and chosen in `config.toml` under `[modules].enabled`.

## Catalog

| Module | Kind | Fits | Thread mode | Schedule (suggested) | Needs | What it does |
|---|---|---|---|---|---|---|
| `librarian` | core | both | no | weekly (Sat) + on demand | nothing | Sole writer of `wiki/`. Processes every agent's submissions, runs structural sweeps. Lossless. |
| `research` | core | both | no | weekly (Sun) | web | Tier-rated research digests on configured topics; standing watches with two independent legs. |
| `ghostwriter` | optional | both | no | on demand | `wiki/concepts/voice.md` filled in | Drafts posts, long-form, threads and memos in the principal's voice. Self-grades A/B/C. Never publishes. |
| `inbox-triage` | optional | both | no | on new filtered mail | the mail filter script | Read-only classifier (urgent / agenda / ignore) for mail that already passed the sender allowlist. Returns JSON. |
| `meeting-prep` | optional | work | no | daily, before first meeting | read-only calendar | Sourced pre-meeting briefs scaled to stakes; debriefs into action items and wiki submissions. |
| `project-tracker` | optional | work | no | weekly (Fri) + daily stale scan | nothing (journal helps) | Evidence-based project records, stale flags, weekly status led by red items and decisions needed. |
| `finance-analyst` | optional | personal | yes | weekly (Sun) | read-only finance data MCP | Conviction × Magnitude rated analysis; confirmation-gated money moves; CPA caveat; Value-Interface tags on every number. |
| `finance-reviewer` | optional | personal | no | per strategic recommendation | `finance-analyst` | Dialectical peer review of strategic finance recommendations until a joint recommendation converges. |
| `health-advisor` | optional | personal | yes | weekly fitness + monthly screening | records in `raw/medical/` | Evidence-tiered interpretation, de-identified health record via the Librarian, care flags. |
| `pet-care` | optional | personal | yes | weekly + monthly | an animal record | Per-animal veterinary records, tiered research, care flags, vet-visit prep. |
| `meal-planner` | optional | personal | yes | weekly kickoff | `household-profile.md` | Weekly menus, full recipes, five-category shopping lists with a mandatory audit line. |
| `price-watch` | optional | personal | no | daily | item files | Per-item price rules with fake-sale detection. Empty days are one line. |

Suggested starting sets:

- **Work profile:** `librarian`, `research`, `inbox-triage`, `meeting-prep`, `project-tracker`, `ghostwriter`.
- **Personal profile:** `librarian`, `research`, `inbox-triage`, plus whichever of `finance-analyst` + `finance-reviewer`, `health-advisor`, `pet-care`, `meal-planner`, `price-watch`, `ghostwriter` you will actually use. Installing a module you never feed just adds noise to the heartbeat.

`finance-analyst` and `finance-reviewer` are a pair: install both or neither.

## What every subagent shares

These hold across every module. They are what make a dozen agents in one folder workable.

- **Bootstrap from files.** The wiring file (`.claude/agents/<slug>.md`) tells the agent to read, in order, `IDENTITY.md`, `SOUL.md`, `SCOPE.md`, `RULES.md`, `MEMORY.md` and `questions.md` from `subagents/<slug>/` on every run. Files are memory; the session is disposable.
- **Write only your own folder.** A subagent writes `subagents/<slug>/**` and nothing else, except Librarian submissions.
- **The Librarian is the only wiki writer.** Everyone else proposes wiki content as a file in `subagents/librarian/submissions/` with a fixed frontmatter (`type: submission`, `source_agent`, `submitted_at`, `proposed_path`, `content_type`, `rationale`). The Librarian integrates, archives, rejects or asks for refinement.
- **Talk only to the main agent.** No subagent messages the principal or another subagent. Cross-domain findings go in the return value (`notes_for_principal`) and the main agent routes them.
- **Thread mode is the one exception.** Thread-capable modules can also run as their own persistent session the principal talks to directly. They answer only in that thread, and anything proactive goes to their append-only `outbox.md`, which the main agent reads for the daily check-in. Contract: `subagents/THREADS.md` in the workspace.
- **Questions file.** When blocked on the principal, a subagent appends to its own `questions.md` (`## Open`, `## Answered`, `## Withdrawn`). The main agent surfaces open questions at session start and records answers; the subagent reads both sections every run, and an answer beats any earlier stance. Ask once.
- **No external action.** No sending, posting, buying, booking or moving money. Output is files and a structured return.
- **Structured returns.** Each SCOPE defines a return shape. The main agent logs digest paths in `memory/active-work.md` and surfaces what matters.
- **Rated outputs.** Every domain module carries an explicit grading scheme (evidence tiers, Conviction × Magnitude, A/B/C, qualification rules, brief depth) and a defended-empty output, so "nothing worth your time" is a valid, one-line answer.
- **MEMORY is curated.** Lessons carry a **Why:** and a **How to apply:**. Keep each file a quick read; move old detail to `memory/archive/`.

## Module layout

```
modules/<slug>/
  MODULE.md                  one-paragraph description, profile fit, inputs, tools/MCP, thread mode, schedule
  agent.md                   wiring, copied to .claude/agents/<slug>.md
  subagent/                  copied to subagents/<slug>/
    IDENTITY.md              the card: name, slug, domain, vibe, reports-to
    SOUL.md                  stance, what good looks like, boundaries
    SCOPE.md                 the contract: domain, triggers, tools, inputs, outputs table, return shape
    RULES.md                 numbered operational rules, failure modes, grading scheme
    MEMORY.md                empty but structured; examples marked fictional
    questions.md             open / answered / withdrawn
    memory/active-work.md    in-flight state
    outbox.md                thread-capable modules only
    <domain dirs>/README.md  what goes in each output folder, with a template
```

Core modules live directly in `template/subagents/<slug>/` and `template/.claude/agents/<slug>.md`, with the same file set.

Placeholders most used in module files: `{{AGENT_NAME}}`, `{{AGENT_SHORT}}`, `{{AGENT_SHORT_LOWER}}`, `{{PRINCIPAL_NAME}}`, `{{WORKSPACE_PATH}}`, `{{TIMEZONE}}`. The init script substitutes these and every other key listed in `config.example.toml` (plus `{{TODAY}}` and `{{YEAR}}`) from `config.toml`. Files in `docs/` are copied into the workspace verbatim, without substitution.

## Adding a module

To install a framework module into an existing workspace, add its slug to `[modules] enabled` in `config.toml` and run `bin/init_workspace.py --config config.toml --dest <workspace> --update-config`. It copies the module's files (never overwriting one that exists) and adds its rows to `HEARTBEAT.md` and `subagents/README.md`.

To design a new one inside an instantiated workspace, run `/new-subagent`. It walks through identity, scope, rules, tools and schedule, writes the files above, wires `.claude/agents/<slug>.md`, and lints the result.

To add one to the framework itself so others can install it:

1. **Pick a narrow domain.** One job, with a clear "done" for each run. If you cannot write its outputs table in five rows, it is two modules.
2. **Copy the closest existing module** as a starting point and rename the slug everywhere.
3. **Write `SCOPE.md` first.** Triggers (each with an exact prompt), tools, inputs, an outputs table listing every path it may write, and the return shape. Anything not in the outputs table is off limits.
4. **Write `RULES.md`.** Number the rules. Include the grading scheme, the defended-empty output, failure modes (source down, data missing, ambiguous input), and the boundaries (own folder only, Librarian for the wiki, no external action, no agent spawning).
5. **Leave `MEMORY.md` empty but sectioned,** with at most one example per section, marked fictional.
6. **Write a README in every output folder** with a file template.
7. **Write `agent.md`.** Frontmatter: `name` (= slug), a generic `description` that says when to invoke it, and `tools` (least privilege; read-only MCP tool names noted for install). Body: bootstrap list using `{{WORKSPACE_PATH}}/subagents/<slug>/...`, task shapes, non-negotiables, return value, and the "you are not in conversation" close.
8. **Decide on thread mode.** Only for domains the principal will want to talk to directly. If yes, add `outbox.md` and the two-modes section to `agent.md`.
9. **Write `MODULE.md`** and add a row to the catalog above and to the Modules table in `template/subagents/README.md` (init builds each installed module's "Installed subagents" row from that table plus the `Thread mode:` line in `MODULE.md`).
10. **Add its dispatch row(s)** if it runs on a schedule: one `module:<slug> | Task | Target time | key | Window | Dispatch |` line per scheduled trigger in the commented "Optional module rows" block of `template/HEARTBEAT.md`. Init moves those lines into the dispatch table when the module is enabled.
11. **Scrub.** No real names, accounts, places, numbers or history from your own deployment. Run a grep for your own identifiers before committing.
