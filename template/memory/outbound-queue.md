# Outbound queue (quiet hours)

Written only by {{AGENT_SHORT}} Ops. Non-urgent outbound messages generated between {{QUIET_START}}:00 and {{QUIET_END}}:00 local are queued here and sent, oldest first, on the first heartbeat inside the window. Urgent items are never queued.

Format: `- [ ] <queued ISO> | to <who> | <verbatim text>`; tick with `- [x] ... | sent <ISO>`.

## Queue
