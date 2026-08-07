# Vault Map

Where things live in this vault. Read this when the task requires creating or moving files.

---

## Folder structure

```

├── CLAUDE.md
├── Maps & Manuals/
│   ├── Me.md                    ← permanent working rules
│   ├── Active Context.md        ← current priorities and open decisions
│   ├── Vault Map.md             ← this file
│   ├── Skill Map.md             ← available workflows and tools
│   └── Writing Style.md        ← use before writing on the user's behalf
├── Ideaverse/
│   ├── Inbox/                   ← drop zone; process and clear
│   ├── Atlas/                   ← permanent reference notes
│   │   └── People/              ← reference notes on people
│   ├── Calendar/                ← daily notes, weekly reviews, meetings
│   ├── Efforts/                 ← active projects (one folder per effort)
│   │   └── (one folder per effort, the live list is the generated table in [[Ideaverse/Efforts/Efforts Index|Efforts Index]])
│   ├── Sources/                 ← raw inputs, not yet processed
│   ├── Outputs/                 ← finished deliverables
│   └── Archive/                 ← inactive or completed material
├── System/                      ← the shared system. Updated as a whole, never edited here
│   ├── Skills/                  ← workflows, tools, data models, templates
│   ├── scripts/                 ← lint, view generation, git hook, integrations
│   └── template/                ← seeds a brand new vault; not live notes
├── Skills/                      ← your own skills, if any. These never leave this vault
└── .claude/                     ← agent adapters (hidden in Obsidian; loaders only, no content)
```

---

## The system half

`System/` is shared with every other installation and updated as a whole. Never edit anything inside it: see [[System/Skills/Tools/Update System|Update System]] for how updates and rollbacks work, and [[System/CHANGELOG|CHANGELOG]] for what changed in each version.

Setting this up on another machine: [[System/SETUP|SETUP]] for macOS, [[System/SETUP-WINDOWS|SETUP-WINDOWS]] for Windows.

---

## Where does a new note go?

| Content type | Destination |
|---|---|
| Files dropped for later processing | `Ideaverse/Inbox/` |
| Raw idea, link, transcript, dump | `Ideaverse/Sources/` |
| Processed concept or framework | `Ideaverse/Atlas/` |
| Active project or ongoing area | `Ideaverse/Efforts/[Effort Name]/` |
| Daily note, meeting, review | [[Ideaverse/Calendar/Calendar\|Calendar]] (`Ideaverse/Calendar/`) |
| Finished document or deliverable | `Ideaverse/Outputs/` |
| Old or inactive material | `Ideaverse/Archive/` |
| Reusable step-by-step process | `Skills/Workflows/` at the vault root, which is yours alone. Never `System/Skills/`, which is shared and replaced on update. To share one, see [[System/Skills/Tools/Update System\|Update System]] |
| Tool or integration documentation | `Skills/Tools/` at the vault root, yours alone |
| Blank starter file | `System/Skills/Templates/`, shared. Copy one; do not edit it in place |
| Instructions about working with the user | [[Maps & Manuals/Me\|Me]] |
| Current priorities and active efforts | [[Maps & Manuals/Active Context\|Active Context]] |

---

## Naming conventions

| Folder | Convention |
|---|---|
| Sources | `YYYY-MM-DD - [Topic].md` |
| Outputs | `YYYY-MM-DD - [Title].md` |
| Calendar | `YYYY-MM-DD` (daily), `YYYY-WXX` (weekly) |
| Efforts | One folder per effort; main note matches folder name |

---

## Key rules

- Do not create subfolders not listed here without updating this map.
- Archive beats deleting. Move things before removing them.
- Raw source files (exports, JSONs, binaries, large imports) that have been fully processed move from `Ideaverse/Inbox/` to `Ideaverse/Archive/[YYYY-MM] - [Project Name]/`. Name the folder after the project the files served, not the file type.
- If an effort has had no updates in 30 days, flag it in [[Ideaverse/Efforts/Efforts Index|Efforts Index]] as Stalled. At 60 days, move to `Ideaverse/Archive/`.
- Do not put project content inside `Maps & Manuals/`.
- Do not put system instructions inside `Ideaverse/`.
- Wikilinks always include the full vault-relative path: `[[Folder/Note Name|Display Name]]`. Never use bare `[[Note Name]]`.
- YAML frontmatter on all Atlas and Effort notes. Standard: [[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]].
- **Some tables in this vault fill themselves in. If you type into one, your text gets wiped the next time they refresh.** They are the ones wrapped in `BEGIN GENERATED` markers. Tell the agent what you want changed instead, and it edits the settings block at the top of the note that the table is built from.
- **There is a safety check that runs before the vault saves, and it refuses to save when something is broken:** a link pointing at a note that does not exist, a missing summary line, a table that would break. It is not a nuisance, it is the thing that stops small mistakes becoming permanent. The agent runs it and fixes what it finds.

---

Last updated: not yet reviewed by this vault's owner. Onboarding sets this.
