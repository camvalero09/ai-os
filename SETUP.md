# Setting up this vault on a new Mac

> **If this vault is yours: this page is not for you.** It is a one-time checklist
> for whoever sets the laptop up with you, and you will never need it again. If you
> are reading it because something is broken, skip to the last section.

**On Windows, use [[SETUP-WINDOWS|SETUP-WINDOWS]] instead.** Several steps genuinely differ.

For the person helping someone else get started, and for whoever comes back to do it a second time.

**Roughly an evening, most of it waiting on downloads and Google.** Work through it with the new owner rather than doing it for them: they need to have seen each piece once, because they will be alone with it later.

The order matters. Each step assumes the one before it worked.

---

## 1. The accounts, before touching the laptop

Two of these cost money or take time, so start them early.

- [ ] **A Claude subscription** for the new owner. Not optional and not shareable.
- [ ] **A Google account** they already use, if Gmail and Calendar are wanted. Nothing to prepare: it is connected with a click inside their AI app during onboarding. **No Google Cloud project and no developer console.** That route still exists as an optional upgrade and is deliberately not part of a first evening.
- [ ] **A Discord account**, if the support bridge is being set up. The design for that lives in the source vault, under the AI OS Replication effort.
- [ ] **Two-factor authentication on Discord**, required if the phone line into the vault is enabled, because their Discord account then becomes a way to reach their files.

---

## 2. Software

- [ ] **Obsidian.** Free, from obsidian.md. This is where they read and write notes.
- [ ] **VS Code.** Free, from code.visualstudio.com. This is where the agent works.
- [ ] **The Claude Code extension for VS Code.** Sign in as *them*, not as you. Easy to get wrong when you are sitting at their machine.
- [ ] **git.** Usually already present. `git --version` triggers the Xcode command line tools install if it is missing.
- [ ] **Python 3.** Also usually present. `python3 --version` should print 3.9 or newer.
- [ ] **Node**, only if the Google MCP server is wanted.

**Why VS Code rather than a terminal.** Claude Code also runs as a plain command line tool, and an earlier version of this checklist assumed that. For someone who has never used a terminal, VS Code is friendlier: a file tree they can click, somewhere to paste credential files, and a built-in terminal for the handful of `python3` and `git` commands, all in one window. There is also a Claude Code desktop app, which may end up being simpler still, but it has not been tested against this vault's skills, settings and git hook. Do not experiment with that on someone's first evening.

Obsidian and VS Code point at the same folder. Neither is optional: Obsidian is for reading and linking, VS Code is where work gets done.

---

## 3. The vault itself

Installing is now a clone and one command. The old routine of tarring a folder
and AirDropping it is gone, and with it the symlink that used to go missing in
transit.

- [ ] Pick a folder and create it. **Avoid iCloud-synced folders**: sync conflicts on a git repo are miserable.
      `mkdir ~/Documents/MyVault && cd ~/Documents/MyVault`
- [ ] Clone the system into it. The folder must be called `System`; everything depends on that name.
      `git clone https://github.com/camvalero09/ai-os.git System`
      If the repository is private, they need to be added to it first, and to sign in to GitHub on their machine.
- [ ] Run the installer.
      `python3 System/scripts/install_vault.py`
      It seeds their own notes from the template, writes the agent settings, creates the gitignored `credentials/` and `logs/` folders, starts git, installs the commit check, generates the index tables, and runs the checker. It refuses to run in a folder that already holds a vault.
- [ ] **Set git identity on the new machine**, or their first commit fails with "Please tell me who you are":
      `git config --global user.name "Their Name"` and `git config --global user.email "their@email"`
- [ ] Fill in `vault.config.json`: their name, timezone, language. It is gitignored and never leaves their machine.

The vault folder can be named anything. The system inside it cannot: it is `System/`.

---

## 4. Open it in Obsidian

- [ ] Open the folder as a vault.
- [ ] If the Google MCP server was installed, exclude its dependencies from the graph: **Settings, Files and links, Excluded files**, add `node_modules`. Otherwise about 155 unconnected nodes appear in graph view.
- [ ] This setting lives in `.obsidian/`, which is **not** in git, so it must be redone on every machine.

---

## 5. Claude Code, and the step that is easy to miss

- [ ] Open the vault folder in VS Code, start Claude Code, and accept the trust prompt **once**. If using the command line instead, run `claude` interactively in the folder and accept it there.
- [ ] Until that is accepted, the permission allowlist in `.claude/settings.json` is silently ignored and every single script call asks for confirmation. It looks like the vault is broken. It is not.

---

## 6. Check the machinery before adding anything real

Do this now, so a problem shows up on nothing rather than on work they care about.

- [ ] `python3 System/scripts/vault_lint.py` should end with "Nothing to fix."
- [ ] `python3 System/scripts/build_views.py` should say views are up to date.
- [ ] `python3 System/scripts/acceptance_test.py` should pass every check. This is the one that answers "would an agent that has never seen this vault find its way", which lint does not.
- [ ] **Prove the hook blocks a bad commit.** Create a note with an invalid `status:` value, try to commit it, watch it fail, delete the note. Worth doing: a hook that silently is not installed looks exactly like a hook that passes.
- [ ] Make a first real commit.

---

## 7. Hand it over to the agent

- [ ] In Claude Code, with the vault folder open, run `/onboard`.

From here the vault sets itself up in conversation with its owner: who they are, what they want it for, their language, their first real project, and connecting Google. See [[System/Skills/Workflows/Onboard|Onboard]].

**Stop being the expert at this point.** They should be the one answering, and the agent should be writing it down. If you answer for them, the vault ends up describing you.

---

## What deliberately is not here

**No scheduled automation.** An earlier version of this system ran weekly maintenance on a timer. It required a macOS Full Disk Access grant, and it failed silently for 19 days without anyone noticing. It was deleted. Weekly upkeep is now a recurring calendar reminder to run `/weekly-maintenance` by hand. If you are tempted to automate something here, read the trap documented in [[System/Skills/Tools/Schedule Task|Schedule Task]] first.

**No shared credentials.** This applies to the optional vault-owned Google server, not to the one-click connectors, which need nothing of the sort. If somebody does set the server up later, every vault authenticates as exactly one account, with its own Google Cloud project and its own OAuth client. Nothing in `*.json.key` or `vault.config.json` is ever copied between vaults. If a tool refuses to run because no account is configured, that is the guard working, not a bug.

**No agent memory.** The behavioural memory an established vault accumulates lives outside the vault and outside git, so a new vault starts without it. Expect it to feel slightly less sharp for the first few weeks while it learns its owner.

---

## If something is wrong

| Symptom | Cause |
|---|---|
| It asks permission for everything, or just seems broken | The trust prompt was never accepted. See step 5. |
| Lint reports broken wikilinks | A note links to something that does not exist. Fix the link, not the lint. |
| A commit is blocked | Read what lint said. Usually views need regenerating: `python3 System/scripts/build_views.py` |
| An index table looks wrong | Never edit it. Fix the note's frontmatter and rerun `build_views.py`. |
| Google tool says no account configured | `google_account` missing from `vault.config.json`. |
| Graph view full of unconnected nodes | `node_modules` not excluded in Obsidian. See step 4. |

---

*This checklist was written before the first real setup. Correct it as reality disagrees, and treat anything that surprised you as something the next person should have been warned about.*
