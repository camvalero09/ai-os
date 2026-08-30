---
id: sessions
type: tool
status: stable
domain: ai_os
updated: 2026-08-30
summary: "Who is working in this vault right now and what nobody has saved. Real script at System/scripts/sessions.py, fed by heartbeats written by hooks in .claude/settings.json."
triggers: "who else is working, another session, is someone in this project, unsaved changes, whose files are these, session table"
expose: false
---

# Sessions

```
python3 System/scripts/sessions.py            # the table
python3 System/scripts/sessions.py --handover # record that this session closed properly
```

Run it at the start of every task. It answers two questions: who else is working, and what is sitting in the vault unsaved.

## Reading the table

| State | Means |
|---|---|
| `ACTIVE` | Pulse under 10 minutes. Someone is working now |
| `idle` | Process alive, pulse older. Someone stepped away |
| `ended` | Process gone. The session is over |
| `ended?` | No pulse for 6 hours, process could not be checked |

**A file no heartbeat claims is unknown, never free.** Only Claude Code writes a heartbeat automatically. Codex, the desktop app and Obsidian do not, so an empty table is not proof the vault is yours.

**When the table names an unidentified agent, ask before editing those files.**

**A session listed as ended without a handover left a debt.** Read its commits and bring the effort note up to date.

## Other agents

Set `AIOS_AGENT` to name the agent and `AIOS_SESSION_ID` to give it an id, then call `--start` once at the beginning and `--beat` as it works.

## Related

[[System/Skills/Workflows/Session Handover|Session Handover]] | [[System/Skills/Tools/Vault Lint|Vault Lint]]
