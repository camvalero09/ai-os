---
id: vault-lint
type: tool
status: stable
domain: ai_os
updated: 2026-07-18
summary: "Health checks for the vault: wikilinks, frontmatter, status vocabulary, entry-point drift, and generated-view sync. Real script at System/scripts/vault_lint.py, enforced by the git pre-commit hook."
---

# Vault Lint

Health checks for the vault. The script lives at `System/scripts/vault_lint.py` (a real file, not a snippet in this note). It runs automatically on every git commit via the pre-commit hook, and weekly via [[System/Skills/Workflows/Weekly Maintenance|Weekly Maintenance]].

---

## How to run

```bash
python3 System/scripts/vault_lint.py
```

From the vault root, the folder that holds `System/`. Exit code 0 means clean; anything else blocks the commit.

The scanner ignores `.git`, `.obsidian`, and `node_modules` directories. These contain repository metadata, Obsidian configuration, or third-party dependency documentation rather than vault notes.

---

## What it checks (errors)

1. **Bare wikilinks:** `[[Note Name]]` without a full vault-relative path. Agents cannot resolve these.
2. **Missing `summary:` field** on Atlas and Effort notes. Agents need it to assess relevance without opening the note.
3. **Broken wikilinks** pointing to files that do not exist.
4. **Entry-point drift:** `CLAUDE.md` and `AGENTS.md` must stay identical in content.
5. **Status vocabulary:** every `status:` value must exist in [[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]].
6. **Generated views out of sync:** runs `System/scripts/build_views.py --check`; fails if any index table no longer matches the frontmatter it is generated from.

## Warnings (reported, non-blocking)

- Active efforts with no update in 30+ days (the stalled rule from [[Ideaverse/Efforts/Efforts Index|Efforts Index]]).

---

## How to fix findings

- **Bare wikilink:** `[[Note Name]]` → `[[Folder/Note Name|Note Name]]`
- **Missing summary:** add one factual sentence to the note's YAML.
- **Broken wikilink:** the target moved or the path is wrong; fix the path.
- **Entry-point drift:** copy the changed content to the other entry file.
- **Status vocabulary:** use a value from the standard, or extend the standard deliberately (structural change protocol).
- **Views out of sync:** `python3 System/scripts/build_views.py && git add -A`

---

## Related

[[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]] | [[Maps & Manuals/Vault Map|Vault Map]] | [[System/Skills/Workflows/Weekly Maintenance|Weekly Maintenance]]
