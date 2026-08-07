---
id: workflow-review-effort
type: workflow
status: stable
domain: ai_os
updated: 2026-05-28
summary: "Check the status of an active effort and refresh its next actions."
---

# Workflow: Review Effort

Use when the user asks for the status of an active project or effort.

---

## Steps

1. Read the Effort folder (main note and any additional files present).
2. Summarize in plain language: goal, current status, what has been done.
3. Identify open questions and blockers.
4. Identify what the next concrete action should be.
5. Update the Next Actions section if the current list is stale or complete.
6. If the effort has not moved in 30+ days, flag it for archiving.

---

## Output format

```
## Effort Review: [Effort Name]

**Goal:** [one sentence]
**Status:** [Active / Stalled / Nearly done / Ready to archive]
**What has been done:** [brief]
**Blockers:** [list or "none"]
**Open questions:** [list or "none"]
**Next actions:** [updated list]
**Flag:** [Archive? Continue? Needs decision?]
```

---

## Related

[[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Workflows/Start New Effort|Start New Effort]] | [[Ideaverse/Efforts/Efforts Index|Efforts Index]] | [[System/Skills/Workflows/Weekly Review|Weekly Review]]
