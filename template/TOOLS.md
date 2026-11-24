# TOOLS.md: Local Notes

Skills define *how* tools work. This file is for the specifics of *this* install: accounts, devices, endpoints, and where credentials live.

## What goes here

- Account identifiers (non-secret)
- MCP servers and what each is for
- Device names, hosts, aliases
- Pointers to where credentials are stored (NEVER the credentials themselves)
- Measured operational limits (login lifetime, rate caps) with the date measured

## Secrets storage convention

**All secrets (API keys, tokens, OAuth refresh tokens) live in the OS keychain. Never in plaintext in this workspace.**

macOS convention:

| Field | Value |
|-------|-------|
| Service name format | `{{AGENT_SHORT_LOWER}}/<purpose>` (e.g. `{{AGENT_SHORT_LOWER}}/github-pat`) |
| Account | `{{OS_USER}}` |
| Add / rotate | `security add-generic-password -U -s "{{AGENT_SHORT_LOWER}}/<name>" -a "{{OS_USER}}" -w` (prompts for the value; avoids shell history) |
| Retrieve | `security find-generic-password -s "{{AGENT_SHORT_LOWER}}/<name>" -w` |
| Delete | `security delete-generic-password -s "{{AGENT_SHORT_LOWER}}/<name>" -a "{{OS_USER}}"` |

On Linux use `secret-tool` (libsecret) with the same service naming; on Windows use Credential Manager.

**When a new secret arrives:**

1. Add it to the keychain under `{{AGENT_SHORT_LOWER}}/<purpose>`.
2. Add a row to the slot inventory below (service, account, purpose, retrieval command). Never the value.
3. Rotation: re-run the add with `-U`. No file change needed.
4. Decommission: delete from the keychain AND remove the row.

**A secret pasted into chat is compromised.** Do not use it. Ask the principal to rotate it at the source.

## Keychain slot inventory

| Service | Account | Purpose | Retrieve |
|---------|---------|---------|----------|
| *(none yet)* | | | |

## MCP servers

| Server | Transport | Endpoint | Scope | Auth | Used by |
|--------|-----------|----------|-------|------|---------|
| *(none yet)* | | | | | |

Notes:

- Register servers the workspace depends on at **user scope** so they load regardless of working directory.
- MCP servers load at session start. After registering one, restart the session before expecting its tools.

## Inbound channels (deterministic filters)

Every channel that can deliver text to a model is listed here with its filter. See `docs/security-model.md`.

| Channel | Account / handle | Access | Filter | Allowlist file |
|---------|------------------|--------|--------|----------------|
| Email | `{{PRINCIPAL_EMAIL}}` or a dedicated agent inbox | read-only OAuth scope | sender allowlist + DMARC/DKIM pass, in code, before any model | `memory/inbox-filter/allowlist.json` |
| *(optional)* SMS / iMessage | the agent's own handle | session plugin | sender-handle allowlist in the plugin, before any model | plugin config |

## Outbound capabilities

List every way the agent can send anything. The default is none.

| Capability | Mechanism | Sender | Recipients (hard-coded) | Rate limit | Token |
|------------|-----------|--------|-------------------------|------------|-------|
| *(none yet)* | | | | | |

## Calendar

| Calendar | Access | Notes |
|----------|--------|-------|
| *(principal's primary)* | read-only | The agent proposes events; it does not write them unless `USER.md` says so. |

## Filesystem conventions

- All git repositories live under one parent directory (for example `~/repos/`). This workspace is `{{WORKSPACE_PATH}}`.
- Scripts live in `scripts/`. Every script the agent relies on for numbers is committed.

## Measured limits

Record operational limits as you measure them, with the date and how to re-measure.

- **Claude Code login lifetime:** *(unmeasured)*. Measure from the timestamp of the last `/login` to the first "login expired" error. Add a heartbeat reminder a few days before it.
- **Web search cap per session:** long-lived sessions can exhaust a per-session search cap shared by all subagents. A session restart resets it.

## Audio transcription (optional)

If you install a local transcriber (for example whisper.cpp), wrap it in `scripts/transcribe.sh` and record the model choice here. Use the larger model whenever names, numbers or decisions matter. Keep transcription local so recordings never leave the machine.
