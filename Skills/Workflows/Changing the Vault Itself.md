---
id: changing-the-vault
type: workflow
status: stable
domain: ai_os
updated: 2026-08-28
summary: "Protocol for changing how the vault works, and where agent-specific files may live."
triggers: "edit Maps and Manuals, change a convention, new workflow, rename folders, bulk edit across notes, add support for another agent, YAML standard"
expose: true
---

# Changing the Vault Itself

A structural change is any edit to `Maps & Manuals/`, YAML conventions, folder structure, a bulk edit across notes, or a new system-level workflow. Content changes to a single Effort or Atlas note are not structural.

## Before

1. State what will change and which files.
2. State why.
3. State what could break or drift.
4. Wait for confirmation if it is irreversible or touches more than three files.

## After

Add an entry to [[Maps & Manuals/Agent Log|Agent Log]] Section 1: what changed, why, and what to watch for. Update `Last updated:` on any `Maps & Manuals` file you touched.

## One home, generated adapters

The vault's law is that the model can change and the system stays. Three rules keep it true:

- **Content has exactly one home, and it is vault Markdown.** Never a file whose name, format or loading order belongs to a vendor.
- **Every agent-specific file is generated, never hand-edited.** `.claude/skills/`, `.agents/skills/`, `CLAUDE.md`, `AGENTS.md`. The test: delete it, regenerate, nothing is lost.
- **Supporting a new agent is a row in a table**, not an edit to a note. Output locations live in `SKILL_TARGETS` in `build_views.py`. A note declares whether it is exposed, never to whom.

Vendor numbers are configuration with a citation, not constants inline in a script.

## Changing the rules themselves

The card in `Maps & Manuals/Me.md` is the only home for rules that apply to every task. Edit it there; `CLAUDE.md` and `AGENTS.md` regenerate from it.

Add a rule only when a mistake has repeated. [[Maps & Manuals/Agent Log|Agent Log]] Section 2 is where candidates accumulate; [[System/Skills/Workflows/Weekly Maintenance|Weekly Maintenance]] promotes or discards them. Do not add temporary reminders.
