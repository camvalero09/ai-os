---
id: workflow-low-token-task-routing
type: workflow
status: stable
domain: ai_os
updated: 2026-05-28
summary: "Navigate the vault efficiently with minimal file reads."
---

# Low Token Task Routing

A workflow for navigating the vault efficiently. Use this to avoid reading unnecessary files and to stop as soon as you have enough context.

---

## Goal

Complete tasks using the minimum number of file reads while maintaining accuracy. Avoid scanning folders or reading raw sources unless explicitly needed.

---

## When to use

Use this as the default navigation pattern for any task in the vault. It is especially important for tasks that span multiple notes or require finding context before acting.

---

## Read order

Read in this order and stop as soon as you have enough context:

1. **[[Maps & Manuals/Me|Me]]**, how to work with the user, output rules, standing preferences
2. **[[Maps & Manuals/Active Context|Active Context]]**, current priorities, active efforts, open loops
3. **[[Maps & Manuals/Vault Map|Vault Map]]**, vault structure and routing rules
4. **[[Maps & Manuals/Skill Map|Skill Map]]**, available workflows and tools
5. **Relevant index**, Atlas Index, Efforts Index, Sources Index, Outputs Index, or Workflow Index
6. **Specific note**, only if the index points to it and it is necessary
7. **Raw source**, only if source-level detail is explicitly required

Stop at step 5 if the index contains enough information to complete the task.

---

## Do not read

- Do not scan folders when an index exists
- Do not open raw source files by default
- Do not read Archive unless explicitly asked
- Do not read all effort notes, read the index first, then only the relevant one
- Do not read Me.md in full on every task if you already have the key preferences in context

---

## Choosing the right folder

| Task type | Start here |
|---|---|
| Something about the user's work or expertise | [[Maps & Manuals/Active Context\|Active Context]] then the relevant Atlas note |
| A specific project or effort | [[Ideaverse/Efforts/Efforts Index\|Efforts Index]] → relevant effort note |
| A concept or piece of knowledge | [[Ideaverse/Atlas/Atlas Index\|Atlas Index]] → relevant Atlas note |
| A raw source that may exist | [[Ideaverse/Sources/Sources Index\|Sources Index]] |
| A previous deliverable | [[Ideaverse/Outputs/Outputs Index\|Outputs Index]] |
| A workflow to follow | [[Maps & Manuals/Skill Map\|Skill Map]] |
| A person the user knows | [[Ideaverse/Atlas/Atlas Index\|Atlas Index]] → `Atlas/People/` |

---

## When to stop reading

Stop reading when you can answer the following:
- What is the task?
- What does the user want as the output format?
- What existing content is relevant?
- What are the constraints (tone, scope, length)?

If you have those four things, start working.

---

## What to update after the task

If the task produced new permanent knowledge → add it to [[Ideaverse/Atlas/Atlas Index|Atlas Index]] and create or update the relevant Atlas note.

If the task advanced an effort → update the effort note and [[Ideaverse/Efforts/Efforts Index|Efforts Index]].

If the task produced a deliverable → add it to [[Ideaverse/Outputs/Outputs Index|Outputs Index]].

If the task added a new source → add it to [[Ideaverse/Sources/Sources Index|Sources Index]].

If a navigation shortcut failed or something required a workaround → add a line to [[Maps & Manuals/Agent Log|Agent Log]].

Do not update files that were only read, not changed.

---

## Output summary format

After completing any task, report:

- **Files read:** list of files opened
- **Files changed or created:** list of files modified
- **Assumptions made:** any gaps filled with inference (flag these)
- **Next useful action:** one suggested next step, if obvious

Keep this short. One or two lines per item is enough.
