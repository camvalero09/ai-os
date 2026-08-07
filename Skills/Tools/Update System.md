---
id: update-system
type: tool
status: active
domain: ai_os
updated: 2026-08-04
summary: "Update the shared system inside a vault to a newer version, or roll back to an older one, without the user ever touching git or resolving a conflict."
triggers: "update the system, check for updates, new version, am I up to date, roll back, undo the update, what changed"
expose: claude_code
---

# Update System

The vault has two halves. `System/` is the shared system, identical in every installation and updated from one place. Everything else is this person's own notes, which never leave their machine except to their own backup.

This note is how the first half moves forward, and how it moves back when an update turns out to be bad.

**Triggers:** update the system, check for updates, is there a new version, am I up to date, roll back, undo that update, what changed.

---

## The rule that makes this safe

**Nobody ever commits inside their own `System/` folder.** It is a read-only copy of shared work. Because nothing local is ever committed there, an update can never produce a conflict for the user to resolve, which is the one thing a non-technical adopter cannot recover from.

The agent runs every command here. The user is asked in plain language and answers yes or no.

---

## Check for an update

```bash
git -C System describe --tags        # the version installed now
git -C System fetch --tags           # ask the server what exists
git -C System tag --sort=-v:refname  # newest first
```

If the newest tag equals the installed one, say so plainly and stop. "You are on the latest version, v1.2" is a complete answer.

## Before offering an update, check nothing local would be lost

```bash
git -C System status --porcelain
```

**If that prints anything, stop. Do not update.** Something inside `System/` has been edited locally. Updating would overwrite it.

Report what changed and ask what to do. Usually this means an improvement was made in the wrong place: it belongs in the shared system repository, not in one person's copy. Offer to send the changed file to the support channel so it can be added upstream properly. See [[System/Skills/Tools/Discord Bridge|Discord Bridge]].

Never resolve this by discarding the local change without saying exactly what will be lost and getting an explicit yes.

## Show what changed, then ask

Read `System/CHANGELOG.md` and show only the entries between the installed version and the newest one. Summarize in the user's own language, in a few lines. Do not paste the whole file, and do not use the word "commit".

Then ask directly: update to v1.2, stay on v1.1, or see more detail.

## Apply it

```bash
git -C System checkout v1.2
```

Then three steps that are not optional, because the rest of the vault is wired to the system:

```bash
cp System/claude-settings.json .claude/settings.json
python3 System/scripts/build_views.py
python3 System/scripts/vault_lint.py
```

The first re-points the agent's permissions and safety hook at the new version. The second regenerates the loader files and index tables from the new skills. The third confirms the vault is still consistent.

If lint reports errors after an update, say so immediately and offer to roll back. An update that breaks the vault should be reversed in the same conversation, not investigated for an hour.

## Roll back

Every version is a tag, so going back is the same operation as going forward:

```bash
git -C System checkout v1.1
cp System/claude-settings.json .claude/settings.json
python3 System/scripts/build_views.py
python3 System/scripts/vault_lint.py
```

Tell the user which version they are on afterwards. Rolling back is normal and cheap, not a failure to apologize for.

---

## For the maintainer: changing the system itself

Only one person writes to the shared system. If that is you, the rule is short: **never edit the `System/` folder inside a vault.** It is a checkout pinned to a version tag, so an edit there reaches nobody, cannot be pushed without care, and blocks the next update.

Work in a separate clone of the system repository instead, checked out on `main`. Four steps, and skipping any one of them means the change reaches nobody:

```bash
cd <authoring copy>
# 1. make the change, then
git add -A && git commit -m "..."   # 2. commit
git tag -a v1.4 -m "..."            # 3. tag: vaults install tags, not commits
git push origin main && git push origin v1.4   # 4. push both
```

Add an entry to `CHANGELOG.md` in the same commit, written for someone who does not code. It is what every adopter's agent reads before asking permission to update.

Then update your own vault the normal way, above. Running the new version yourself before anyone else does is the point of being an installation rather than a special case.

**Versions are immutable once published.** Never move a tag that exists on the remote: a vault that already installed it would silently hold different files under the same name, and rollback stops meaning anything. Cut a new version instead, even for a one-line fix.

**Set `system_authoring_path`** in your vault's `vault.config.json` to that clone. The lint check then warns you, on every save, if system work is sitting uncommitted, unpushed, or committed with no new tag. Leave it unset if you do not author the system.

---

## Reporting a problem or contributing an improvement

Adopters do not have write access to the shared system, by design. One person maintains it.

When this vault produces a workflow that would help everyone, it is written to the vault's own `Skills/` folder first, where it is used and proven. If it turns out to be genuinely general, send the file through the support channel with a sentence on what it does. See [[System/Skills/Tools/Discord Bridge|Discord Bridge]].

Do not send anything containing personal content. A workflow that names a specific person, employer, or project is not general yet, and the boundary check in [[System/Skills/Tools/Vault Lint|Vault Lint]] will say so.

---

## Where the line falls

| Lives in `System/` | Lives in the vault |
|---|---|
| Shared skills and workflows | This person's own skills |
| The scripts: lint, generated views, safety check, integrations | Their notes, efforts, and sources |
| The canonical settings file | Their `Me.md`, `Active Context.md`, `Agent Log.md` |
| The changelog and setup guides | Their `vault.config.json` and credentials |

Anything under `System/` is shared with every other installation. That is the whole rule, and it is why nothing personal is ever written there.

---

## Related

[[System/Skills/Tools/Vault Lint|Vault Lint]] | [[System/Skills/Tools/Discord Bridge|Discord Bridge]] | [[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Skill Map|Skill Map]]
