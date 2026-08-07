---
id: yaml-metadata-standard
type: data_model
status: stable
domain: ai_os
updated: 2026-07-07
---

# YAML Metadata Standard

Standard for YAML frontmatter in this vault. YAML is for routing, filtering, indexing, and export. Reasoning and nuance go in the Markdown body.

For the summary of levels, see also [[Maps & Manuals/Vault Map|Vault Map]].

---

## Principle

- Markdown body is for humans and reasoning.
- YAML is for routing, filtering, indexing, and exporting.
- Do not put long explanations in YAML.
- Do not invent metadata. If a value is unknown, leave the field blank or write `unknown`.
- Do not add YAML to all existing notes at once. Add it when a note needs it.

---

## Level 1, No YAML

Use for notes where metadata adds no value:

- Raw captures
- Quick thoughts
- Temporary notes
- Meeting dumps
- Long transcripts
- Article dumps
- Inbox files

---

## Level 2, Minimal YAML

Use for notes that benefit from basic routing and filtering:

- Atlas notes
- Effort notes
- Workflow notes
- Decision notes
- Output notes
- Source cards (processed summaries, not raw captures)

**Minimum fields:**

```yaml
---
id:
type:
status:
domain:
updated:
summary:
next:        # Effort notes only, and not optional in practice
---
```

`next:` is easy to miss and expensive to miss. It is the only source of the
next-action column in [[Maps & Manuals/Active Context|Active Context]] and
[[Ideaverse/Efforts/Efforts Index|Efforts Index]], so an effort created without
it shows a blank there and stays blank until somebody notices. Write it as the
single next action, specific enough to start on without rereading the note.

### `effort_refs:` (skill notes only, optional)

Set to `intentional` on a skill note that deliberately names a specific effort, with an inline comment saying why.

Lint warns when a note under `Skills/` names an effort, because that is how a reusable skill quietly turns into a one-project skill. Some references are legitimate: a tool note may name the effort that owns a shared account in order to state a safety boundary, and an example is clearer with a real name. This field marks those so the warning keeps pointing at real drift instead of becoming noise everyone ignores.

Do not use it to silence a genuine problem. If a skill only makes sense for one project, it belongs in that effort's folder.

The `summary:` field is mandatory on all Atlas and Effort notes. Write one sentence describing what the note contains. This allows agents to assess whether a note is relevant without opening it, they read the index, check summaries, and only open notes that match. Keep it factual and specific, not generic.

**Example, Atlas note:**

```yaml
---
id: fraud-and-risk-domain-overview
type: atlas
status: stable
domain: fraud
updated: 2026-05-28
summary: "Master reference for the user's professional domain, mapping core fraud problem areas, signals, and key concepts for agents working on fraud tasks."
---
```

**Example, Effort note:**

```yaml
---
id: career-positioning
type: effort
status: active
domain: career
updated: 2026-05-28
next: "Draft the two-line positioning statement and test it on three people this week."
summary: "Active effort to define and communicate the user's professional identity as a fraud and risk specialist targeting senior fintech and AI-enabled roles."
---
```

---

## Level 3, Rich YAML

Use only when the note may become a tracker, dashboard, CSV export, JSON export, or database row (e.g., Supabase).

Add only the fields that are actually needed. Do not fill in every possible field.

**Example, Startup idea (potential Supabase row):**

```yaml
---
id: startup-idea-fraud-saas
type: startup_idea
status: draft
domain: startup
updated: 2026-05-28
stage: raw_idea
validated: false
source_note: "Ideaverse/Sources/2026-05-26 - Startup Ideas Raw.md"
---
```

---

## Recommended types

| Type | Used for |
|---|---|
| `atlas` | Permanent knowledge notes |
| `effort` | Active projects and areas |
| `source` | Raw input files |
| `source_card` | Processed source summary |
| `workflow` | Step-by-step processes |
| `template` | Blank starter files |
| `tool` | Tool or integration documentation |
| `data_model` | Data standards and schemas |
| `decision` | Recorded decisions |
| `output` | Finished deliverables |
| `meeting` | Meeting notes |
| `daily` | Daily notes |
| `startup_idea` | Startup idea notes |
| `fraud_rule` | Antifraud rule documentation |
| `metric` | Fraud or product metric definitions |

---

## Recommended statuses

| Status | Meaning |
|---|---|
| `raw` | Unprocessed, just captured |
| `draft` | Being worked on |
| `active` | In use or in progress |
| `stable` | Settled, unlikely to change often |
| `needs_review` | Flagged for a review pass |
| `processed` | Source has been extracted into Atlas |
| `archived` | No longer active, kept for reference |
| `deprecated` | Superseded, should not be used |
| `closed` | Effort finished; folder not yet moved to Archive |

This vocabulary is enforced by `System/scripts/vault_lint.py`. Extending it is a structural change.

---

## Fields consumed by generated views

`System/scripts/build_views.py` generates the index tables (Efforts Index, Atlas Index, Active Context efforts table, Sources Index, Outputs Index) from frontmatter. Fields it reads:

- `status`, `updated`, `summary` (all note types)
- `next:` on Effort notes: the current next action, one line. Shown in Active Context and Efforts Index.
- `processed_into:` on Source notes: semicolon-separated vault paths of the Atlas notes the source produced.

To change anything shown in those tables, edit the note's frontmatter and run the script. Never edit the tables directly.

---

## Domains

`domain:` groups notes that belong to the same area of life or work, so a person
can ask "everything about X" and get it. **There is no fixed list.** The right set
depends entirely on whose vault this is, and a vault that inherits somebody else's
categories files everything under whichever one is least wrong.

**Start with these four**, which almost everyone needs:

| Domain | Covers |
|---|---|
| `ai_os` | This vault and the system itself |
| `work` | Whatever they are paid for: clients, employer, projects |
| `money` | Income, invoices, savings, investments, tax |
| `life_admin` | Housing, health, immigration, vehicles, paperwork |

**Then add theirs during onboarding.** An economist tracking consulting contracts
needs `consulting`, not `work`. Someone building a company needs `startup`. Somebody
living abroad usually wants a domain for that country's paperwork specifically,
because it behaves nothing like the rest of life admin.

Two rules that keep the list useful:

- **Split when a domain gets crowded**, not before. Ten notes under `work` is fine.
  Sixty is a signal that two or three real areas are hiding inside it.
- **Never invent one on the fly for a single note.** If nothing fits, use the closest
  and say so, then raise it as a question. A domain used once is noise, and the next
  agent will pick a different one for the same kind of note.

Whatever set they end up with, record it here so it is the same next month.

---

## Organisation-attributed knowledge

When a note contains knowledge derived from a specific company or employer, add two optional fields:

```yaml
tags: [delivery_hero]
source_org: delivery_hero
```

`tags:` is recognised by Obsidian natively and appears in the tag pane, clicking the tag shows all notes from that org. `source_org:` is a machine-readable field for filtering and future export.

Current org tags in use: `delivery_hero`

**When to create a subfolder instead of using tags:** when org-attributed notes across Atlas and Skills exceed ~6 files, a dedicated subfolder (for example a folder named after the organization) may make more sense than tags alone. Until then, tags are sufficient.

---

## Rules

- Keep YAML short.
- Do not put reasoning or nuance in YAML, put it in the Markdown body.
- Do not invent metadata. Leave unknown fields blank or write `unknown`.
- Preserve the source note path in `source_note` when converting notes to structured data.
- Do not add YAML to all existing notes at once. Add it progressively.
- Add `tags` and `source_org` to any note whose content comes from a specific employer or organisation.

---

## Related

[[Maps & Manuals/Vault Map|Vault Map]] | [[System/Skills/Workflows/Convert Note to Structured Data|Convert Note to Structured Data]] | [[Maps & Manuals/Skill Map|Skill Map]]
