---
id: personal-google
type: tool
status: active
domain: ai_os
updated: 2026-08-05
summary: "Vault-owned Gmail, Calendar and Drive access for the personal Google account, independent of any agent-specific connector."
triggers: "personal Gmail, personal email, draft from my email, organize inbox, Gmail labels, download attachment, personal Google Drive, find my Drive file, personal calendar, schedule meeting, create calendar event"
expose: true
---

# Personal Google

## Use this, not the host's own Google tools

**First, is this set up at all?** Most vaults will not have it: since 2026-08-07 onboarding connects Gmail and Calendar through the AI app's own one-click connectors instead, and this server is an optional upgrade. If `credentials/` holds no Google token, use the host's connectors, say that is what you did, and do not treat it as a fault or offer to fix it. The rest of this section applies only where both exist.

Whichever agent is running probably also carries its own Google integration: Claude has the claude.ai connectors, Codex has a curated `google-calendar` plugin. Those advertise themselves with long lists of trigger phrases and will be reached for first unless told otherwise. **They are the fallback. This is the default.**

Three reasons it matters, none of them cosmetic:

- **Identity is checked here and nowhere else.** This tool refuses to run unless it authenticates as exactly the account in `google_account`. A host connector will happily use whichever Google account that platform is signed into, which on a shared or work machine is not necessarily the right one.
- **The guardrails live here.** Sending mail is not exposed at all. Deleting mail is not exposed. Drive is read-only. Calendar writes demand an explicit confirmation field, and changing or deleting an event demands the exact event ID. None of that constrains a host connector.
- **It is the same everywhere.** This behaves identically whichever agent is driving, which is the whole point of a model-independent system. Host connectors differ between vendors and change without notice.

**Say which one was used.** If the host's connector was used because this was genuinely unavailable, state that in the reply rather than letting the difference pass unnoticed: the permissions are not the same.


Use `System/scripts/personal_google.py` for work involving the personal Google account named in `vault.config.json`. This is a vault-owned integration for Gmail, Drive, and Google Calendar available to any terminal-capable agent. It is independent from OpenAI connectors and from any project-specific or organizational Google account.

**Triggers:** personal Gmail, personal email, draft from my email, organize inbox, Gmail labels, personal Google Drive, find my Drive file, personal calendar, schedule meeting, create calendar event.

---

## Account boundary

This tool must authenticate exactly as the account set in `google_account` in `vault.config.json`, or in the `VAULT_GOOGLE_ACCOUNT` environment variable. There is no default: if neither is set the tool refuses to run rather than guessing. It rejects any other Gmail or Drive identity before saving or using a token.

Never use this personal account as the official sender for a shared or organizational mailbox. Project-specific account rules remain authoritative.

## Capabilities and guardrails

The OAuth grant contains these exact scopes:

- `gmail.modify`: required to read messages, create drafts, and modify message labels.
- `drive.readonly`: required to search, inspect, download, and export files from the personal Drive.
- `calendar`: required to read availability and events and to create, reschedule, invite, cancel, move, and otherwise manage events and secondary calendars.

Google's `gmail.modify` scope technically permits sending, but this local client intentionally implements no send command. It also excludes deleting email and moving messages to Trash or Spam. Drive has an API-enforced read-only scope and cannot upload, rename, move, share, trash, or delete files.

Calendar write operations are exposed because the user explicitly authorized full calendar management. The client supports availability queries, bounded event searches, event creation and updates, attendee notifications, reminders, recurrence resources, conference data, moving events between calendars, event cancellation, and secondary-calendar creation, updates, and deletion. It does not expose Calendar ACL or sharing changes.

Before any Calendar write, read the existing calendar state and normalize the date, time, and timezone. Creates require `--confirm-create`. Updates, moves, and event deletion require the exact event ID twice. Calendar updates and deletion require the exact calendar ID twice. Deleting the primary calendar is blocked. External invitations and cancellation notices require an explicit `--send-updates all` or `externalOnly`; the safe default is `none`.

Creating a draft is allowed when the user asks for a message they will review and send manually. Sending always requires a separately approved capability and explicit instruction.

Gmail uses labels rather than conventional folders. Removing `INBOX` archives a message. Adding or removing `UNREAD` changes its read state. Use user label names for organization.

Attachments download to a new local path and never overwrite an existing file. Identify the attachment by `--filename`, or by `--attachment-id` from `get-message` when two attachments on the same message share a name. The parent directory must already exist.

## Independent OAuth setup

Use a dedicated Google Cloud project, such as `Vault Personal`. Do not reuse an OAuth client from another project.

1. Enable the Gmail API, Google Drive API, and Google Calendar API in the personal Cloud project.
2. Configure the OAuth audience as External.
3. While the app is in Testing, add the configured account as a test user.
4. Add the `gmail.modify`, `drive.readonly`, and `calendar` scopes to the app's Data Access configuration.
5. Create an OAuth client of type Desktop app.
6. Download the client JSON.
7. Open `credentials/personal_google_oauth_client.json.key` in the IDE and replace the placeholder with the complete downloaded JSON. Never paste it into chat.
8. Restrict the file to mode `0600`.
9. Run the authorization command below and choose the configured account.

Testing authorizations expire after seven days. Move the app to In Production and reauthorize, so the stored refresh token is no longer subject to the Testing-mode seven-day lifetime. Google may still revoke it after a password or security change, manual revocation, prolonged disuse, client deletion, or a scope change. Google allows limited personal-use apps to remain unverified, but the account may show an unverified-app warning. Do not make the client public or add unknown users.

## Commands

```bash
python3 System/scripts/personal_google.py authorize
python3 System/scripts/personal_google.py doctor

python3 System/scripts/personal_google.py search-email 'from:example@example.com newer_than:30d'
python3 System/scripts/personal_google.py get-message MESSAGE_ID
python3 System/scripts/personal_google.py list-labels
python3 System/scripts/personal_google.py create-label 'Projects/Example'
python3 System/scripts/personal_google.py organize-message MESSAGE_ID --add-label 'Projects/Example' --remove-label INBOX

python3 System/scripts/personal_google.py download-attachment MESSAGE_ID \
  --filename 'report.pdf' \
  --output /absolute/path/report.pdf

python3 System/scripts/personal_google.py create-draft \
  --to recipient@example.com \
  --subject 'Subject' \
  --body-file /absolute/path/body.txt

python3 System/scripts/personal_google.py drive-search 'document name'
python3 System/scripts/personal_google.py drive-info FILE_ID
python3 System/scripts/personal_google.py drive-download FILE_ID --output /private/tmp/document.pdf --format pdf

python3 System/scripts/personal_google.py list-calendars
python3 System/scripts/personal_google.py list-events \
  --calendar-id primary \
  --time-min '2026-07-20T00:00:00+02:00' \
  --time-max '2026-07-27T00:00:00+02:00'
python3 System/scripts/personal_google.py freebusy --request-file /absolute/path/freebusy.json
python3 System/scripts/personal_google.py create-event \
  --calendar-id primary \
  --event-file /absolute/path/event.json \
  --send-updates all \
  --confirm-create
python3 System/scripts/personal_google.py update-event EVENT_ID \
  --calendar-id primary \
  --event-file /absolute/path/event-patch.json \
  --confirm-event-id EVENT_ID
```

Draft bodies come from a UTF-8 local file so the content does not need to appear in shell history. Downloads never overwrite an existing local file.

## MCP server

`System/scripts/personal_google_mcp.mjs` exposes the same Python client and token through 24 explicit MCP tools. It does not implement separate Google authentication or duplicate business rules. MCP standardizes agent access; Google OAuth still controls the underlying token lifetime.

### Agent-neutrality rule

The MCP server belongs to the vault, not to Codex, Claude, Cursor, or another host. `System/scripts/personal_google_mcp.mjs`, `System/scripts/personal_google.py`, the OAuth files, and this note are the canonical integration. Never move the implementation or credentials into an agent-specific configuration directory.

Every MCP-compatible host launches the same stdio command. Replace `<vault>` with the absolute path to this vault folder, because MCP host registrations cannot use relative paths:

```bash
/opt/homebrew/bin/node "<vault>/System/scripts/personal_google_mcp.mjs"
```

Host registrations are thin local adapters and may differ by product. The Codex registration below is one tested example, not the source of truth. Claude Code, Cursor, VS Code, or another MCP host should point its own MCP configuration to the same command and arguments. An agent without MCP can call `System/scripts/personal_google.py` directly, so the capability remains usable even when the host changes.

The local server uses the stable v1 official TypeScript SDK over stdio. Dependencies are pinned in `package.json` and `package-lock.json`; `node_modules/` is local and gitignored.

```bash
npm install
npm run mcp:personal-google
```

One tested host adapter, Codex registration completed on 2026-07-18:

```bash
codex mcp add personal-google -- \
  /opt/homebrew/bin/node \
  "<vault>/System/scripts/personal_google_mcp.mjs"
codex mcp get personal-google
```

The server code and credentials are vault-owned, but each MCP host needs its own local registration pointing to that same command. Restart the host or open a new session after registration because MCP tool discovery normally occurs at session start.

MCP tools preserve the CLI boundaries: Gmail draft creation but no send or delete; Gmail label organization; read-only Drive; full Calendar event and secondary-calendar management with exact-ID confirmations; and no Calendar ACL changes.

## Secrets and revocation

The following files are local, mode `0600`, and covered by the vault's `*.json.key` Git ignore rule:

- `credentials/personal_google_oauth_client.json.key`
- `credentials/personal_google_oauth_token.json.key`

Revoking the app grant in the configured account, or removing the personal token, disables the tool without affecting other Google projects or native agent connectors.

## Verification

After authorization, always run:

```bash
python3 System/scripts/personal_google.py doctor
```

The result must report the configured account for Gmail, Drive, and Calendar, the three exact scopes, and `false` for Gmail send, email deletion, Drive write, and Calendar ACL exposure. The MCP server was independently tested through the official host-neutral MCP client, not only through Codex. Handshake, 24-tool discovery, identity verification, and read calls across Gmail, Drive, and Calendar all passed.

## When two agents are open at once

One account, one stored token, and any number of agents that might be running. When one of them refreshes the token, a connection already open inside another goes stale and every call fails, usually with nothing more helpful than "request failed". The account is fine. The running connection is not.

Observed on 2026-08-04 with the Anthropic and OpenAI desktop apps open together: one refreshed the token, the other's calls stopped working within the same minute, and the command line kept working throughout.

What to do, in order:

1. `python3 System/scripts/personal_google.py doctor`. If it reports the right account and scopes, nothing is broken and nobody needs to reauthorize.
2. Use the command line for whatever the user actually asked for. It reads the token fresh each time, so it is unaffected.
3. To restore the connection inside the app, restart that app.

**Never respond to this by reauthorizing, deleting the token, or creating a second one.** Two tokens for one account turns an annoyance into a real problem. Say plainly what happened: another app refreshed the connection, this one needs restarting, nothing was lost.

## Related

[[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Skill Map|Skill Map]]
