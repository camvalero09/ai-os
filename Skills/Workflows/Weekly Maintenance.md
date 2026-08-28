---
id: weekly-maintenance
type: workflow
status: stable
domain: ai_os
updated: 2026-08-06
summary: "Agent-run weekly upkeep: lint, regenerate views, flag stale efforts, draft the weekly review with decision-forcing questions, commit. The human reviews the draft; the machine does the bookkeeping."
triggers: "weekly maintenance, weekly review, vault upkeep, run maintenance"
expose: true
effort_refs: intentional  # provenance: points at the effort that recorded why automation was removed
---

# Weekly Maintenance

Supersedes the manual choreography in [[System/Skills/Workflows/Weekly Review|Weekly Review]]: an agent executes this; the user only reviews the draft and makes the decisions.

**Run this manually.** The user runs `/weekly-maintenance` in an agent session in the vault. Set a recurring calendar event carrying the prompt as the reminder. A reminder needs no permissions and cannot fail silently, which a scheduled job can.

Skipping a week breaks nothing; the next run picks up whatever drifted.

This vault deliberately schedules nothing. A scheduled job for this once failed silently for 19 days while saving only one command a week, and it required a macOS privacy permission to work at all. `System/scripts/weekly_maintenance.sh` still exists and works if run directly, but nothing schedules it. See [[System/Skills/Tools/Schedule Task|Schedule Task]] for why a reminder beats a scheduled job here.

## Steps (agent)

1. **Check for a system update.** `git -C System fetch --tags`, then compare `git -C System describe --tags` with the newest tag. This is the only step that reaches the network, and it is why it lives here: the save-time notice only reports versions already downloaded, so without this weekly fetch a waiting update stays invisible forever.

   If there is a newer version, follow [[System/Skills/Tools/Update System|Update System]]: show the user the plain-language changelog entries between their version and the newest, ask, and only then check it out. Do not update silently, and do not update at all if `git -C System status` is not clean.

2. **Compare this laptop's records against GitHub**: `python3 System/scripts/check_history_remote.py`. Files that record what happened only ever grow, so any difference means one was altered here. Every other protection lives on this machine and can be gone around from this machine; this is the one that notices afterwards. If it reports anything, stop and show the user before doing anything else.
3. **Check the size of the agent transcript folders**: `du -sh ~/.claude/projects ~/.codex/sessions`. These grow without limit and hold a plain-text copy of every file any session read, including any credential one happened to open. They sit outside the vault, so nothing in `.gitignore` protects them. If a month is finished and its work is recorded in the vault, move that month to the Trash rather than deleting it, and tell the user that emptying the Trash is what actually removes it. One month of desktop-app sessions measured 180MB on 2026-07.
4. Run `python3 System/scripts/vault_lint.py`. Fix what it reports; regenerate views if out of sync. Run `python3 System/scripts/vault_metrics.py` and include its table in the draft; trends live in `logs/metrics.csv`.

   **Work the expired-content warnings, do not just read them.** Lint flags past dates in `next:` fields and ageing "as of" claims. Each one is a fact that was true when written and is not now, sitting in a file that reads as current. For each: has it happened, is it overdue, or should it be relabelled as historical? Fix the note, do not silence the warning.
5. Read [[Maps & Manuals/Active Context|Active Context]] and [[Ideaverse/Efforts/Efforts Index|Efforts Index]]. For each active effort: check `git log --since="7 days ago"` for movement; flag efforts crossing 30 days (stalled) or 60 days (propose archiving).
6. Draft `Ideaverse/Calendar/YYYY-WXX - Weekly Review.md` from the [[System/Skills/Templates/Weekly Review|Weekly Review]] template: what moved (from git log), what stalled, what is next week's focus.

   Open the draft with one line: **"Knowledge current through: YYYY-MM-DD"**, the date of the oldest thing the vault still presents as current. Usually the oldest unresolved expired-content warning. It is the single most useful number in the review, because it says how far the vault can be trusted without checking.
7. **Read every project's Open questions table** and put anything open past 30 days into the draft, with its age and the answer as it stands. Report them; do not push for a decision on any of them. The protocol that used to do that was switched off on 2026-08-06 for raising unrelated items mid-session, and the weekly draft is the place these belong precisely because it is a moment the user chose to look at everything.
8. Check `Ideaverse/Inbox/` and `Ideaverse/Sources/` for unprocessed items older than a week; list them in the draft.
9. Link-quality pass on notes created or heavily edited this week (from git log): each should link to the related notes an agent would want next (parent effort, relevant Atlas notes), not just be reachable from an index. Add missing cross-links; lint only guarantees reachability, not usefulness.
10. Propose (do not apply) any Active Context priority changes in the draft.

   **Promote repeated mistakes into rules.** Read [[Maps & Manuals/Agent Log|Agent Log]] Section 2. For anything that has now happened twice, draft the standing rule it implies and propose it for [[Maps & Manuals/Me|Me]] or the relevant domain note; once the user accepts it, delete the entries it came from, because a lesson that has graduated must live in exactly one place. Delete any entry older than 90 days that never produced a rule change. If Section 2 has gained nothing since the last review, say so in the draft: an empty log usually means sessions are skipping step 6 of [[System/Skills/Workflows/Session Handover|Session Handover]], not that no mistakes were made.
11. **Repo hygiene.** Several agents work in this vault and each leaves artefacts that `git status` never shows, so nothing surfaces them until someone goes looking:

   ```
   git worktree list                          # Claude Code leaves worktrees under .claude/worktrees/
   git for-each-ref | grep -v refs/heads      # Codex leaves checkpoint refs under refs/codex/
   du -sh .git                                # should stay in single-digit MB
   ```

   Report anything beyond the main worktree and `refs/heads/main`. Do not delete without checking first: `git worktree list` entries may hold uncommitted work, and a ref may be the only thing pointing at something wanted. Verify with `git status` inside the worktree and `git log main..<branch>` before removing.

   On 2026-07-31 a forgotten worktree held 482 MB and a leftover Codex ref silently kept 356 MB of deleted objects alive, defeating a history purge. Both were invisible to every normal command.

12. Commit: stage the explicit paths this run touched, then `git commit -m "Weekly maintenance YYYY-WXX"`. Push if a remote is configured. Do not use `git add -A`: another session may be mid-edit, and a broad stage silently commits its unfinished work under this message. If `git status` shows changes this run did not make, leave them unstaged and name them in the draft.

## Reading the vault, not just checking it

Two framings worth applying while drafting, borrowed from the wider practice of auditing agent context.

**The four ways context breaks.** Tag anything you notice with the one it feeds, because the fix differs:

- **Poisoning**, something false sitting where an agent reads it as true. A passed deadline still written in future tense. A snapshot that no longer matches reality. The most dangerous, because agents do not doubt their context.
- **Bloat**, too much loaded every session so the important part gets lost. Watch the word count of [[Maps & Manuals/Me|Me]] and [[Maps & Manuals/Active Context|Active Context]]; they are paid for on every single call.
- **Confusion**, something needed is missing or something irrelevant is present. Unlinked notes, a rule that lives only inside one project folder where no fresh session will find it.
- **Clash**, two places saying different things, usually old versus new. The same fact in two notes at two ages.

**Where a fact belongs.** Anything loaded every session should be *stable*: rules, preferences, conventions. Anything with a shelf life (a number, a status, a date) belongs in the effort note it concerns, with the always-loaded file holding a pointer rather than a copy. A live fact baked into a preloaded file is guaranteed to go stale, in the one place the agent trusts most.

The generated tables handle this automatically. The hand-written sections of Active Context, Current priorities and Open decisions, do not, and are where to look first.

## Rules

- Never mark a decision as made; only the user closes decisions.
- Effort `updated:` fields reflect real work, not maintenance runs.
- If lint cannot be brought to zero, say so in the draft rather than skipping checks.
