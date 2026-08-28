---
id: workflow-capture
type: workflow
status: stable
domain: ai_os
updated: 2026-05-28
summary: "Save raw thoughts, links, transcripts, and dumps into the vault inbox or sources."
triggers: "save this, capture, new source, transcript, article, link dump"
expose: true
---

# Workflow: Capture

Use when the user pastes raw thoughts, links, transcripts, article notes, screenshots, or messy ideas that should not be lost.

**Destination:** `Ideaverse/Sources/`

---

## Steps

1. Save the raw content as-is. Do not restructure or interpret it yet.
2. Use this filename format: `YYYY-MM-DD - [Topic or Source Name].md`
3. Add a brief header with three fields:
   - **What it is:** one sentence describing the content type and origin
   - **Why it might matter:** one sentence on potential relevance
   - **Suggested next step:** Capture only / Process into Atlas / Link to Effort
4. Do not create Atlas notes or Effort links unless explicitly asked.
5. Confirm what was saved and where.

---

## When to escalate

If the content has immediate, obvious relevance to an active Effort, note the connection at the bottom of the source note as: `Possibly relevant to: [[Effort Name]]`. Do not restructure the source.

---

## Related

[[Maps & Manuals/Skill Map|Skill Map]] | [[Maps & Manuals/Vault Map|Vault Map]] | [[System/Skills/Workflows/Process Source into Atlas|Process Source into Atlas]]
