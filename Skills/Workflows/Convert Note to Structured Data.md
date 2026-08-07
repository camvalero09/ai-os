---
id: workflow-convert-note-to-structured-data
type: workflow
status: stable
domain: ai_os
updated: 2026-05-28
summary: "Export a note as CSV, JSON, or database-ready format."
---

# Convert Note to Structured Data

Use this workflow when a note needs to be turned into structured output: a CSV row, JSON object, or database-ready record (e.g., Supabase).

Do not run this by default. Only run it when explicitly requested.

---

## When to use

- the user asks to export a note or set of notes as structured data
- A note is ready to become a tracker row or database entry
- A collection of notes needs to be tabulated for analysis

---

## Steps

### 1. Identify the note type

Read the note and match it to a type from [[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]]:
`atlas`, `effort`, `source`, `source_card`, `workflow`, `decision`, `output`, `startup_idea`, `fraud_rule`, `metric`, etc.

If the type is unclear, ask before proceeding.

### 2. Identify the relevant data model

Check `Skills/Data Models/` for a schema that matches the note type.

If no schema exists, extract the fields that are clearly present in the note. Do not invent fields or values.

### 3. Extract fields

Extract only values that are explicitly stated in the note.

- If a value is implied but not stated, flag it as `inferred` rather than filling it in silently.
- If a value is missing entirely, leave the field blank or use `null`.
- Do not summarize or paraphrase in a way that changes the meaning.

### 4. Preserve the source note path

Always include the source note path in the output:
```
source_note: "Ideaverse/Atlas/Fraud and Risk - Domain Overview.md"
```

This makes it possible to trace the structured data back to the original note.

### 5. Choose the output format

| Format | When to use |
|---|---|
| YAML frontmatter | Adding metadata to the note itself |
| Markdown table | Showing structured data inline in a note |
| CSV | Export to spreadsheet or Supabase import |
| JSON | API use or structured export |

Only produce CSV or JSON when explicitly requested.

### 6. Create or update a tracker (if requested)

If the output should feed a tracker note (e.g., a startup ideas tracker), add a row to the tracker note. Do not create new tracker notes unless asked.

### 7. Do not convert everything at once

Convert one note at a time. Do not bulk-convert the vault unless explicitly instructed.

---

## What to flag

- Values that were inferred rather than directly stated
- Fields that had no data in the source note
- Any ambiguity in how a field was interpreted

---

## Related

[[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]] | [[Maps & Manuals/Skill Map|Skill Map]] | [[Ideaverse/Atlas/Atlas Index|Atlas Index]]
