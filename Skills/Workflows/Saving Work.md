---
id: workflow-saving-work
type: workflow
status: stable
domain: ai_os
updated: 2026-09-04
summary: "Make a Git checkpoint that saves one unit of work without swallowing another session's files."
triggers: "save this, commit, checkpoint, stage, git, save my work, record what changed"
expose: true
---

# Saving Work

The obligation is in the shared rules: checkpoint a completed unit, stage only what that unit changed, and never push unless asked. This note holds the commands.

The whole point is that a vault is a shared folder. Another agent, another window, or the last session can leave files staged, and an ordinary commit would sweep them into yours. Then two changes travel under one message and neither can be reverted alone.

---

## The four steps

**1. See what is actually changed, and by whom.**

```bash
git status --porcelain
python3 System/scripts/sessions.py    # who else is live, when the script exists
```

Anything you did not touch belongs to someone else. Leave it.

**2. Add new files by their exact paths.**

```bash
git add "Ideaverse/Efforts/Name/New Note.md"
```

This step is not optional for new files, and it is the one people skip. The commit in step 4 takes a path list, and it cannot see a file git has never heard of. Skip this and the new note silently stays out of the commit.

**3. Read the diff you are about to commit.**

```bash
git diff -- <paths>
git diff --cached -- <paths>
```

Not a summary of it. The diff.

**4. Commit only those paths.**

```bash
git commit -o -F <message file> -- <paths>
```

`-o` commits the listed paths only, ignoring whatever else sits in the index. `-F` takes the message from a file, which keeps multi-line messages and quotes intact.

---

## The message

Say what changed and why in the first line, then the reasoning if it needs one. End with attribution, which the commit check enforces:

```
Agent: <name and model>
Session: <id from logs/sessions/>
```

A commit with no `Agent:` line is treated as the owner's own and is not checked.

---

## When a checkpoint fails

The pre-commit check runs the vault lint and blocks on real problems. That is the system working.

**Do not** work around it with `--no-verify`, and do not report the work as done. Fix what it names, or preserve the changes and report the failure with the exact command to retry.

---

## What never happens here

- **No `git add -A`, no `git add .`, no `git commit -a`.** All three swallow other sessions' work.
- **No push.** Pushing happens when the owner asks, never as a session-closing habit.
- **No amending or rebasing a commit that is already pushed.** Someone else may hold it.
- **No committing inside `System/`.** It is a read-only checkout updated by tag; see [[System/Skills/Tools/Update System|Update System]].

---

## Related

[[System/Skills/Tools/Sessions|Sessions]] | [[System/Skills/Tools/Vault Lint|Vault Lint]] | [[System/Skills/Workflows/Session Handover|Session Handover]] | [[System/Skills/Tools/Update System|Update System]]
