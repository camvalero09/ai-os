---
id: personal-outlook
type: tool
status: active
domain: ai_os
updated: 2026-07-20
summary: "Read the user's personal Outlook/Hotmail mailbox through a vault-owned Microsoft Graph integration. Read-only: search, list, read messages, download attachments. No send, delete, or write."
triggers: "outlook, hotmail, personal outlook, old email account, search my outlook, read my hotmail, check my other mailbox"
expose: true
---

# Personal Outlook

Use `System/scripts/personal_outlook.py` for work involving the user's personal Outlook/Hotmail mailbox. Vault-owned integration usable by any terminal-capable agent, independent from claude.ai connectors (which do not support personal Microsoft accounts).

**Triggers:** Outlook, Hotmail, old email account, bank or supplier emails, search my Outlook.

---

## Capabilities and guardrails

Strictly read-only by scope design. The OAuth grant contains exactly:

- `Mail.Read`: search, list, and read messages and download attachments.
- `User.Read`: identity verification only (`doctor` command).
- `openid offline_access`: sign-in and token refresh.

No send, delete, move, draft, or any mailbox write is requested from Microsoft or implemented in the client. Attachment downloads never overwrite an existing local file.

## Authentication

OAuth 2.0 device code flow against the `consumers` tenant (the only reliable path for personal Microsoft accounts). Tokens refresh automatically; if the refresh token dies (password change, revocation, long disuse), re-run `authorize`.

### One-time Entra app registration

1. Sign in at https://entra.microsoft.com with the personal Microsoft account (any Microsoft account works; the app just needs to allow personal accounts).
2. Microsoft Entra ID, App registrations, New registration.
3. Name: `Vault Outlook`. Supported account types: **Personal Microsoft accounts only**. No redirect URI needed.
4. In the app's **Authentication** blade: set "Allow public client flows" to **Yes** and save.
5. In **API permissions**: add Microsoft Graph, Delegated, `Mail.Read` (`User.Read` is there by default). No admin consent needed.
6. Copy the **Application (client) ID** from Overview into `credentials/personal_outlook_client.json.key` (open in the IDE, replace the placeholder; never paste into chat).
7. Run `python3 System/scripts/personal_outlook.py authorize`, open the printed URL, enter the code, sign in with the Hotmail account.

## Commands

```bash
python3 System/scripts/personal_outlook.py authorize
python3 System/scripts/personal_outlook.py doctor

python3 System/scripts/personal_outlook.py search-email 'insurance claim'
python3 System/scripts/personal_outlook.py list-messages --sender noreply@example-bank.com --since 2024-01-01
python3 System/scripts/personal_outlook.py list-messages --folder Inbox --top 20
python3 System/scripts/personal_outlook.py get-message MESSAGE_ID
python3 System/scripts/personal_outlook.py download-attachment MESSAGE_ID ATTACHMENT_ID --output /private/tmp/file.pdf
python3 System/scripts/personal_outlook.py list-folders
```

`search-email` is full-text across the mailbox. `list-messages` supports exact sender and date filters and folder scoping. `get-message` prints the body as plain text and lists attachment IDs.

## Secrets and revocation

Local, mode `0600`, covered by the `*.json.key` gitignore rule:

- `credentials/personal_outlook_client.json.key` (client ID)
- `credentials/personal_outlook_token.json.key` (token cache, auto-created)

Revoke by removing the app under https://account.live.com/consent/Manage or deleting the token file. Neither affects the Google integration or any other credential.

## Verification

After authorization, always run:

```bash
python3 System/scripts/personal_outlook.py doctor
```

It must report the expected Hotmail address and `false` for send, delete, and write.

## Related

[[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Tools/Personal Google|Personal Google]]
