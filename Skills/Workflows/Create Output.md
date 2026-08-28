---
id: workflow-create-output
type: workflow
status: stable
domain: ai_os
updated: 2026-08-28
summary: "Produce a finished file rather than pasting content into chat, with the right destination, naming and quality checks."
triggers: "create a document, write a report, make a deck, build a spreadsheet, draft a letter, produce a deliverable, save this as a file"
expose: true
---

# Workflow: Create Output

Use when the user needs something finished: email, Slack message, SQL, report, document, template, negotiation draft, presentation outline.

**Destination:** `Ideaverse/Outputs/[Category]/YYYY-MM-DD - [Title].md`

---

## Steps

1. Identify the audience and goal. If not stated, infer and confirm.
2. Identify the right format and tone (see [[Maps & Manuals/Me|Me]], Communication style).
3. Draft the output in full. Make it copy-ready.
4. Save to Outputs with the correct naming convention.
5. Summarize what was created and suggest any follow-up.

---

## Output categories (subfolders to use)

- `Slack Messages/`
- `Emails/`
- `SQL/`
- `Documents/`
- `Executive Updates/`
- `Negotiation/`
- `Templates/` (if the output is reusable)

Create a subfolder only when there are multiple outputs of the same type. Otherwise save directly in `Outputs/`.

---

## Quality check before saving

- Is this copy-ready? Could the user send or use it as-is?
- Is the tone right for the audience?
- Is the ask or point obvious?
- For SQL: does it run? Are assumptions noted?
- For German/legal content: are facts separated from interpretations?

---

## Related

[[Maps & Manuals/Skill Map|Skill Map]] | [[Maps & Manuals/Me|Me]]

---

## When a task would produce a file, create the file

Do not output the content to chat. Read the relevant skill note first: it carries rules that prevent common errors.

- Save to `Ideaverse/Outputs/` unless Camilo specifies a path, or to the effort's own `Outputs/` folder when it belongs to a project.
- Name it `YYYY-MM-DD - [Title].[ext]`.
- Give it a real `summary:` in the settings block. That field is what agents read to decide whether to open it.
- Confirm the path afterwards with a one-line summary of what was produced.

**Presentations:** convert to images and inspect before declaring done. Use a subagent for fresh eyes.
**Spreadsheets:** zero formula errors before delivery. Verify with a formula check.

## What not to do to the vault

- Do not create files or folders that were not requested, or duplicate a note that exists.
- Do not overwrite any file without first saying what will change.
- Do not delete raw sources.
- Reference a document or transaction by its exact file, date and identifier. Camilo keeps several versions of most things.
- Updating rows in shared data: match every identifying field, never one. A receipt number can legitimately span several rows.
