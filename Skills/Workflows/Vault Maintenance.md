---
id: vault-maintenance
type: workflow
status: stable
domain: ai_os
updated: 2026-06-18
summary: "Step-by-step vault maintenance workflow to keep Active Context current, prune stale entries, run lint, and commit a clean state to git."
---

# Vault Maintenance

Run this during [[System/Skills/Workflows/Weekly Review|Weekly Review]], or any time the vault feels stale, inconsistent, or out of sync with current reality.

**Triggers:** "vault feels stale", "clean up the vault", "consolidate", "prune", "vault maintenance", "update the vault", or when lint returns issues.

---

## When to run

- Weekly, as part of [[System/Skills/Workflows/Weekly Review|Weekly Review]]
- After a period of heavy vault activity (many new notes, bulk edits)
- Before starting a new major effort or project
- Any time Active Context no longer reflects what is actually happening

---

## Step 1, Update Active Context

Open [[Maps & Manuals/Active Context|Active Context]] and verify each section is accurate:

**Current priorities:** Do the 3 items still reflect what actually matters right now? Remove anything completed or deprioritised. Add anything new.

**Active efforts table:** For each effort, check the next action is still the actual next action. Update status if an effort has stalled or completed.

**Open decisions table:** Has any decision been made since the last update? Remove it from the table and log it in the relevant Effort note as "Decided: [what was decided] on [date]." Apply the decision-forcing protocol to anything that has been sitting open for more than 2 weeks.

Update `Last updated:` to today.

---

## Step 2, Run the lint script

```bash
python3 "<vault>/System/scripts/vault_lint.py"
```

Fix any issues before continuing. A clean lint pass is required before committing. See [[System/Skills/Tools/Vault Lint|Vault Lint]] for how to interpret results.

---

## Step 3, Prune Agent Log

Open [[Maps & Manuals/Agent Log|Agent Log]] Section 2 (errors and misroutes).

- If an error entry is older than 90 days and has not produced a standing rule change: delete it.
- If the same error type has appeared 2+ times: encode a rule in [[Maps & Manuals/Me|Me]] and note it as resolved.
- Section 1 (structural changes): keep all entries. These are the audit trail, do not prune.

---

## Step 4, Check for stalled or completed efforts

Open [[Ideaverse/Efforts/Efforts Index|Efforts Index]] and review each effort:

- **No updates in 30 days:** flag status as `Stalled` in the index table.
- **No updates in 60 days:** move the effort folder to `Ideaverse/Archive/` and remove from the Active table.
- **Completed:** move to `Ideaverse/Archive/` immediately. Do not let completed work sit in the active folder.

---

## Step 5, Check for Atlas duplication

Scan [[Ideaverse/Atlas/Atlas Index|Atlas Index]] for notes that may now overlap significantly. If two notes cover the same topic from different angles, consider merging them. Do not merge speculatively, only when there is clear duplication.

If a new Atlas note is needed based on recent work, create it now following the YAML standard in [[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]].

---

## Step 6, Update YAML dates

For any note that was meaningfully updated during this maintenance pass, update its `updated:` field to today's date.

```yaml
updated: 2026-06-18
```

---

## Step 7, Commit to git

```bash
cd "<vault>"
git add -A
git commit -m "Vault maintenance, YYYY-MM-DD"
```

This creates a clean snapshot after maintenance. If anything breaks between now and the next maintenance run, you can restore to this state.

---

## Maintenance log

After completing, add a one-line entry to [[Maps & Manuals/Agent Log|Agent Log]] Section 1 only if structural changes were made. Routine maintenance (updating Active Context, pruning old log entries) does not need to be logged.
