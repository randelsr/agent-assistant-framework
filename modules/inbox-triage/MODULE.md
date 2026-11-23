# Module: inbox-triage

A read-only classifier for email that has already passed the workspace's deterministic sender allowlist and authentication checks. It sorts each message into urgent, agenda or ignore, extracts dates, deadlines and asks, suggests calendar entries, and flags links that failed the phishing check. It has the Read tool and nothing else, so a hostile message can at worst be misclassified; the allowlist in code, not this agent, is the security boundary. The Ops session decides what to do with its JSON (alert now, add to the daily agenda, or drop).

- **Profile fit:** both (work: a shared team or assistant inbox; personal: a household inbox).
- **Inputs it needs:** the workspace mail filter writing one JSON file per passed message (with optional `links` results from the deterministic link checker). The trusted-sender list comes from `config.toml` `[comms].trusted_senders`.
- **Tools / MCP:** none. Read only. The mail fetch runs in a script, not in this agent.
- **Thread mode:** no.
- **Schedule:** dispatched by the Ops heartbeat when new filtered mail exists; every 15 to 30 minutes outside quiet hours is a good default.
- **Install:** copy `subagent/` to `subagents/inbox-triage/` and `agent.md` to `.claude/agents/inbox-triage.md`. {{AGENT_NAME}} maintains this agent's `MEMORY.md`, since the agent cannot write.
