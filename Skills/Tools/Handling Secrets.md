---
id: handling-secrets
type: tool
status: stable
domain: ai_os
updated: 2026-08-28
summary: "Create and store credentials without ever writing them into a transcript."
triggers: "api key, token, credentials.json, secret, password, .env, service account, authorize an integration"
expose: true
---

# Handling Secrets

## Creating one

Write a placeholder file with paste instructions. Tell the owner to open it in the IDE and replace the content there. **Never ask them to paste a secret into chat.**

Secrets live in `credentials/`, never inside `System/`. Add any new secret type to `.gitignore` before use. The root `.gitignore` already covers `credentials.json`, `*.json.key` and `.env`.

## Never read one

Every session writes a full transcript to `~/.claude/projects/` or `~/.codex/sessions/`, in plain text, **outside the vault where `.gitignore` cannot reach it.** A credential read once is copied there permanently.

- To confirm a credential exists, check that the path exists.
- To confirm it works, make a call with it and report whether the call succeeded.
- Reading it to "verify the format" writes the secret into a second file.

Rotating a secret does not remove it from transcripts written before the rotation. A revoked key is still readable in last month's log.

## Pruning

Old transcripts hold every file any session read. Move finished months to the Trash, and tell the owner that emptying the Trash is the step that actually removes them.

Found 2026-08-07: three July transcripts held a Google service-account private key in full, while `.gitignore` had kept that same file out of git perfectly since the day it was created.
