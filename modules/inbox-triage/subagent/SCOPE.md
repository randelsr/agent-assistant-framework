# SCOPE: Inbox Triage

## Domain

Read-only classification of email that already passed the workspace's deterministic sender allowlist and authentication checks (see the security docs and `TOOLS.md` for the mail filter). The filter writes one JSON file per message; the Ops session hands this agent the paths.

## Trigger

{{AGENT_NAME}}'s Ops session dispatches it via the Agent tool with `subagent_type: inbox-triage` whenever the mail filter has new files (suggested: every 15 to 30 minutes during waking hours, {{TIMEZONE}}). The prompt carries today's date and time and the list of file paths.

## Tools

`Read` only.

## Inputs

- The JSON message files named in the prompt. Each carries headers, body text, and an optional `links` list produced by the filter's deterministic link check (`verdict: pass | fail`, `reasons`, and for passed links the fetched page `text` and a `login_or_payment_page` flag).
- This folder's `RULES.md` and `MEMORY.md`.

## Outputs

None on disk. The return value is the output. Because it cannot write, its `MEMORY.md` and `questions.md` are maintained by {{AGENT_NAME}} from {{PRINCIPAL_NAME}}'s feedback on past classifications.

## Return value

JSON only, no prose:

```json
{"items": [
  {"file": "<path>",
   "class": "urgent|agenda|ignore",
   "who": "<person or team it concerns, or null>",
   "summary": "<one plain sentence>",
   "when": "<ISO date/time it is about, or null>",
   "deadline": "<ISO date of any action deadline, or null>",
   "action": "<what someone must do, or null>",
   "calendar_suggestion": "<'Title, ISO start, ISO end, location' or null>",
   "why_urgent": "<only if urgent: which rule>",
   "link_warning": "<only if a link failed the check or a page asks for login or payment>"}
]}
```

One item per file, in the order given.
