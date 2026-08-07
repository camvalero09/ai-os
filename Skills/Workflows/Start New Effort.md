---
id: workflow-start-new-effort
type: workflow
status: stable
domain: ai_os
updated: 2026-05-28
summary: "Open a new project or area of work with the standard folder and note structure."
---

# Workflow: Start New Effort

Use when something becomes an active project or ongoing area of work worth tracking.

**Destination:** `Ideaverse/Efforts/[Effort Name]/`

---

## Steps

1. Create the folder: `Ideaverse/Efforts/[Effort Name]/`
2. Create the main note using the [[System/Skills/Templates/Effort|Effort]] template. Name it the same as the folder.
3. **Fill in the frontmatter first**, before the prose. `id`, `type: effort`, `status`, `domain`, `updated`, `summary` and `next`. The vault check refuses to save an effort without a `summary`, and an effort without a `next` shows a blank next-action column in every generated table forever. If you are writing the file directly rather than through Obsidian, put today's real date in `updated`.
4. Fill in: goal, context, scope, and why this matters now.
5. Add 2-3 concrete next actions to the Next actions section.
6. Link to any relevant Atlas notes or Sources at the bottom, using full paths.
7. **Run `python3 System/scripts/build_views.py`.** Until this runs, the effort exists but appears in no index and nothing links to it, so the check will report it as unreachable. This is the step people miss.
8. **Never add the effort to [[Ideaverse/Efforts/Efforts Index|Efforts Index]] by hand.** That table is generated from frontmatter and hand-editing it fails the check. Step 7 puts it there.
9. If this becomes a current priority, add it to the Current priorities list in [[Maps & Manuals/Active Context|Active Context]], and add a routing row if there is a category of question that should jump straight to it. **Editing anything in `Maps & Manuals/` is a structural change**, so it carries the protocol in [[Maps & Manuals/Me|Me]]: say what will change before doing it, add an [[Maps & Manuals/Agent Log|Agent Log]] entry afterwards, and refresh that file's `Last updated:`. Easy to miss, because the edit itself is one line.

---

## When to create additional files

Start with a single note. Add separate files only when the effort grows enough to need them:
- `Plan.md` when there are more than 5 ordered steps
- `Decisions.md` when a key decision has been made and the reasoning matters
- `Open Questions.md` when there are 3+ unresolved questions blocking progress
- `Outputs/` subfolder when the effort produces deliverables

---

## Effort archiving rule

If an effort has had no updates in 30 days, review it. Either update it or move the folder to `Ideaverse/Archive/`, creating that folder if it does not exist yet. It leaves [[Ideaverse/Efforts/Efforts Index|Efforts Index]] by itself once moved and `build_views.py` has run.

---

## Related

[[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Templates/Effort|Effort]] template | [[Ideaverse/Efforts/Efforts Index|Efforts Index]] | [[System/Skills/Workflows/Review Effort|Review Effort]]
