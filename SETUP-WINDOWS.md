# Setting up this vault on Windows

The Mac version of this checklist is in [[SETUP|SETUP]]. This one covers the same ground for Windows, where a handful of things genuinely differ.

**Roughly an evening**, most of it waiting on downloads. Work through it *with* the new owner rather than for them: they will be alone with this later, so they need to have seen each piece once.

---

## 1. Accounts, before touching the laptop

- [ ] **A Claude subscription** for the new owner. Not optional and not shareable.
- [ ] **A Google account** they already use, if Gmail and Calendar are wanted. Nothing to prepare: it is connected with a click inside their AI app during onboarding. **No Google Cloud project and no developer console.** That route still exists as an optional upgrade and is deliberately not part of a first evening.

---

## 2. Software

- [ ] **Obsidian**, free from obsidian.md. This is where they read and write notes.
- [ ] **VS Code**, free from code.visualstudio.com. This is where the agent works.
- [ ] **The Claude Code extension** for VS Code. Sign in as *them*, not as you.
- [ ] **Git for Windows**, from git-scm.com. Take the defaults. This also installs Git Bash, which the lint hook needs.
- [ ] **Python 3**, from python.org, **not** the Microsoft Store version. On the first installer screen tick **"Add python.exe to PATH"**. This is the single most common thing to get wrong, and skipping it means nothing else in this checklist works.

Check both in a new terminal:

```
git --version
python --version
```

**On Windows the command is `python`, not `python3`.** Everywhere the rest of the documentation says `python3`, type `python`. If `python` opens the Microsoft Store, the PATH tickbox was missed: reinstall from python.org with it ticked.

---

## 3. The vault

There is no zip any more. The system is cloned from GitHub and one command does the rest.

- [ ] **Avoid OneDrive-synced folders.** Windows puts Documents in OneDrive by default, and sync conflicts inside a git repository are genuinely painful. Use a path outside OneDrive if Documents is synced.
- [ ] Create the vault folder and open a terminal in it. In VS Code: **Terminal, New Terminal**.

```
mkdir C:\Users\<name>\Vault
cd C:\Users\<name>\Vault
```

- [ ] Clone the system into it. The folder must be named `System`; everything depends on that name.

```
git clone https://github.com/camvalero09/ai-os.git System
```

If the repository is private, they must be added to it first and signed in to GitHub on this machine.

- [ ] Set the git identity, or the first commit fails with "Please tell me who you are":

```
git config --global user.name "Their Name"
git config --global user.email "their@email.com"
```

- [ ] Run the installer. It seeds their notes, writes the settings, creates the gitignored `credentials` and `logs` folders, starts git, installs the commit check, builds the index tables and runs the checker.

```
python System/scripts/install_vault.py
```

- [ ] Fill in `vault.config.json`: their name, timezone, language. It is gitignored and never leaves the machine.

The vault folder can be named anything. The system inside it cannot: it is `System`.

- [ ] Create their config file:

```
copy vault.config.example.json vault.config.json
```

Then open it in VS Code and fill in name, timezone and language. It is gitignored and stays on their machine.

---

## 4. Obsidian

- [ ] Open the folder as a vault.
- [ ] If the Google integration is installed later, exclude its dependencies from the graph: **Settings, Files and links, Excluded files**, add `node_modules`.
- [ ] That setting lives in `.obsidian\`, which is not in git, so it must be redone on every machine.

---

## 5. Claude Code, and the step everyone misses

- [ ] Open the vault folder in VS Code, start Claude Code, and **accept the trust prompt once**.
- [ ] Until that is accepted, the permission list in `.claude\settings.json` is silently ignored and every command asks separately. It looks like the vault is broken. It is not.

---

## 6. Check the machinery before adding anything real

- [ ] `python System/scripts/vault_lint.py` should end with "Vault is clean."
- [ ] `python System/scripts/build_views.py` should report views already up to date.
- [ ] **Prove the hook blocks a bad commit.** Create a note with an invalid `status:` value, try to commit it, watch it fail, then delete the note. A hook that silently is not installed looks exactly like one that passes, so this is worth two minutes.
- [ ] Make a first real commit.

---

## 7. Hand over to the agent

- [ ] In Claude Code, with the vault folder open, run `/onboard`.

From there the vault sets itself up in conversation with its owner. **Stop being the expert at this point.** They answer, the agent writes. If you answer for them, the vault ends up describing you.

---

## What differs from macOS, and one thing you should know

**File permissions on credentials are not enforced here.** On macOS these tools refuse to read a credential file unless it is `chmod 600`, so a mistake is caught. Windows has no equivalent: files report the same permissions regardless of their real access rules, so that check is skipped rather than faked.

The practical consequence: on Windows, a credential file is protected by living in the user's own profile and nothing else. That is normal for a personal laptop, and worth knowing if the machine is shared or if anyone else has an administrator account on it.

**The git hook is a shim, not a symlink.** `install_hook.py` writes a two-line script into `.git\hooks\` that calls the real one. Symlinks need developer mode or admin rights on Windows and do not survive zip transfer, so this avoids the problem rather than working around it.

**No scheduled automation, on any platform.** An earlier version ran weekly upkeep on a timer, required an operating-system privacy exception, and failed silently for nineteen days before anyone noticed. It was deleted. Weekly upkeep is now a calendar reminder to run `/weekly-maintenance` by hand.

**No inherited memory.** An established vault accumulates behavioural memory that lives outside the vault and outside git. A new vault starts without it and will feel slightly less sharp for the first few weeks while it learns its owner.

---

## If something is wrong

| Symptom | Cause |
|---|---|
| `python` opens the Microsoft Store | Installed from the Store, or PATH not ticked. Reinstall from python.org. |
| `python3` not recognised | On Windows the command is `python`. |
| `git` not recognised | Git for Windows not installed, or the terminal predates the install. Open a new one. |
| Every command asks permission | Trust prompt not accepted. See step 5. |
| A commit is blocked | Read what lint said. Usually: `python System/scripts/build_views.py` |
| An index table looks wrong | Never edit it by hand. Fix the note's frontmatter and rerun `build_views.py`. |
| The hook never fires | Rerun `python System/scripts/install_hook.py`, then retest with a deliberately broken note. |
| Google tool says no account configured | `google_account` missing from `vault.config.json`. |

---

*Written before the first Windows setup. Correct it as reality disagrees, and treat anything that surprised you as something the next person should have been warned about.*
