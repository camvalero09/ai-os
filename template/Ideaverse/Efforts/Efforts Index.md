# Efforts Index

Single view of all efforts. The tables below are generated from each effort note's YAML frontmatter by `System/scripts/build_views.py`. To change a status, goal, or next action: edit the effort note's frontmatter, then run the script (the pre-commit hook enforces sync).

---

<!-- BEGIN GENERATED: efforts-tables -->
## Active

| Effort | Goal (one line) | Next action | Last updated |
|---|---|---|---|

## Stalled (no movement in 30+ days)

*None.*

## Closed or archived

*None yet.*
<!-- END GENERATED: efforts-tables -->

---

## Rules

- Effort status, goal (summary), next action, and dates live in each effort note's YAML frontmatter: that is the single source of truth.
- New efforts created with [[System/Skills/Workflows/Start New Effort|Start New Effort]] appear here automatically once the note has frontmatter.
- Active efforts with no update in 30+ days move to Stalled automatically. After 60 days, move the folder to `Ideaverse/Archive/` and set `status: archived`.
- Never edit the generated tables by hand.
