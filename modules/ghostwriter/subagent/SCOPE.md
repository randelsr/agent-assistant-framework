# SCOPE: Ghostwriter

## Domain

Drafts in {{PRINCIPAL_NAME}}'s voice. Supported formats:

- Social post, long-form platform style (default 1,000 to 2,000 characters)
- Blog / long-form article (default 600 to 1,200 words)
- Thread (default 5 to 10 posts)
- Internal memo or announcement (default 300 to 800 words)

Voice is calibrated to `wiki/concepts/voice.md`, which {{PRINCIPAL_NAME}} fills in (registers, signature phrases, anti-patterns, sign-offs, sample links). Default register: written long-form.

## Triggers

On demand only. {{AGENT_NAME}} delegates via the Agent tool with `subagent_type: ghostwriter` and a prompt naming:

- topic and angle
- format
- length (if overriding the default)
- source material (links, notes, frameworks)
- whether to include calibration notes

No schedule. Ghostwriter does not self-trigger.

## Tools

`Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch`. No Agent tool.

## Inputs

| Path | What |
|---|---|
| `wiki/concepts/voice.md` | **Primary calibration source.** Read every run. |
| `wiki/writings/` | Published corpus. Voice anchors. |
| `raw/writings/` | Verbatim originals, if deeper sampling is needed. |
| `wiki/concepts/` | {{PRINCIPAL_NAME}}'s frameworks and theses. |
| `wiki/initiatives/` | Current work context. |
| `USER.md` | Style rules for anything published under {{PRINCIPAL_NAME}}'s name. |
| `raw/journal/` | Recent context when a draft references current events. |

## Outputs

| Path | What |
|---|---|
| `subagents/ghostwriter/drafts/YYYY-MM-DD-<slug>.md` | One file per draft; revisions update the same file. |
| `subagents/ghostwriter/MEMORY.md` | Voice learnings, calibration heuristics, edge cases. |
| `subagents/ghostwriter/memory/active-work.md` | Revision-cycle state. |
| `subagents/ghostwriter/questions.md` | Blocked on {{PRINCIPAL_NAME}}. |

**Never writes `wiki/`.** When {{PRINCIPAL_NAME}} publishes a draft, {{AGENT_NAME}} drops the published copy in `raw/writings/` and submits it to the Librarian.

## Report back to {{AGENT_NAME}}

```
- task_type: draft | revision | calibration_query
- draft_path: <absolute path; omit for calibration_query>
- format: <format>
- length: <word_count | char_count | post_count>
- tier: A | B | C
- topic_anchor: <corpus post or concept page this echoes, or "none, Tier C">
- calibration_notes: <only if requested>
- source_failures: []
- notes_for_principal: <what is worth surfacing about this draft>
```
