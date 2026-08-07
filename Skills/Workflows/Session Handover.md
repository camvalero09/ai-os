---
id: session-handover
type: workflow
status: stable
domain: ai_os
updated: 2026-08-06
summary: "Close a working session so the next agent can act correctly without ever seeing the conversation: update the effort note, refresh frontmatter, wire routing, sweep the chat for orphaned facts and filter them against the keep test, externalize deadlines, record one outside observation, commit only your own paths, then write the human wrap-up."
triggers: "wrap up, close the session, handover, hand over, let's finish for today, pick up tomorrow, end of session"
expose: claude_code
---

# Session Handover

Close a session so the next agent, human or AI, can act correctly without ever seeing this conversation. Chat history dies with the session; the vault is the handover.

**Triggers:** wrap up, close the session, handover, let's finish for today, pick up tomorrow.

---

## The one test

Before ending, ask: could a fresh agent, reading only Me.md, Active Context, and the relevant effort note, continue this work without mistakes? If anything needed to pass that test exists only in the conversation, the handover is not done.

## Principles

1. **Write to where the next agent will look.** The reading path is [[Maps & Manuals/Me|Me]] then [[Maps & Manuals/Active Context|Active Context]] then the effort note. A summary in the chat's final message is a handover to the user, not to the system.
2. **Facts carry identifiers.** Ticket numbers, radicados, dates, amounts, file paths, email subjects. "The ticket from earlier" dies with the session; "ticket 46903162214, due 2026-08-11" survives.
6. **Corrections propagate everywhere.** When a fact you wrote earlier turns out wrong, hunt down every copy: body text, drafts, and especially the frontmatter `summary:` field, because that is what agents read to decide whether to open the note. A stale confident claim is worse than a missing one.
7. **Separate four states explicitly:** what happened (with evidence), what was decided (by whom), what is pending (owner + deadline), what is blocked (on what, until when). Blurring pending and blocked makes the next agent re-analyze instead of act.
8. **Record verification status, not just conclusions.** "Proven from the source document" and "the user recalls, unverified" get different markers. Unverified claims that reach external documents are how sessions ship errors.

## Steps at session close, in order

1. **Rewrite the project note to say what is true now.** Not append. Replace anything the session made untrue, delete what stopped mattering, and keep it short enough to read in one screen. This note answers "where does this stand", and if it cannot be read quickly it has failed. The settings block at the top is part of the rewrite, not a separate step: `updated:` date; `next:` as a concrete dated action ("file SFC queja 2026-08-12 15:00 Berlin"), never "continue the work"; `summary:` reflecting the current truth after all corrections.
2. **Add one row to `Project_log.md`**: date, which agent, what happened. Append only, newest at the top. Never edit or reorder an existing row; correct one by adding another. The commit check refuses a log that lost a line.
3. **Close every question this session answered.** Open questions live in a table in the project note, and a question leaves it by having its answer written into the row, never by being deleted. Skipping this is why a resolved contract question sat listed as blocking for two days.
4. **File any output into the project's own `Outputs/` folder**, with a settings block carrying a real `summary:`. If it concluded something, write that conclusion into the project note now: a generated table can list a file, it cannot know what the file decided.
5. **Wire the entry points**: if the topic is new, escalated, or time-critical, add or update the routing row and priority line in [[Maps & Manuals/Active Context|Active Context]] so discovery is one hop.
6. **Sweep the chat for orphaned facts, then filter them**: any number, decision, identifier, credential location, or constraint that was only said in conversation is a candidate. This is the step most sessions skip. Then apply the keep test below, because the opposite failure is real: a vault that records everything becomes one no agent can read cheaply. calendar events (via [[System/Skills/Tools/Personal Google|Personal Google]]) for time-critical ones, explicit dates in `next:` for the rest. A deadline buried in prose is a missed deadline.
7. **Log this session's mistakes to [[Maps & Manuals/Agent Log|Agent Log]] Section 2**: one line each, in the format `YYYY-MM-DD | what went wrong | fix applied or rule to add`. Log a mistake if it cost real time, sent the session down a wrong path, or would have been avoided by a rule that does not exist yet. Do not log typos, one-off tool errors, or anything already fixed by an existing rule. This is the step that makes the vault learn: Section 2 is scanned during [[System/Skills/Workflows/Weekly Maintenance|Weekly Maintenance]], and anything appearing twice becomes a standing rule in [[Maps & Manuals/Me|Me]]. An empty session is fine, but say so rather than skipping the step silently.
8. **Record one outside observation in `Private/Outside View.md`**: what you observed about how the user worked this session, drawn from behaviour rather than from anything they stated about themselves. Insert directly under the marker near the top of that file, and do not read the entries below it first: independent reads are the entire point, and an agent that reads last month's entry writes an agreement with it. Observations only, never advice, one or two at most, and "nothing new this session" is both a valid entry and the most common one. Read that file's own header before writing the first time. Nothing recorded there may be quoted back to the user in session or used to decide anything, here or later.
9. **Lint, regenerate views, commit your own work only**: `python3 System/scripts/build_views.py`, then git commit with a message stating what changed. Stage the explicit paths this session edited, never `git add -A` or a directory you did not touch, per the rule in [[Maps & Manuals/Me|Me]]. If `git status` shows changes you did not make, another session is probably live: leave them unstaged and name them in the wrap-up. The commit makes the handover durable; the pre-commit hook enforces hygiene.
10. **Write the human wrap-up last**: TLDR of what happened plus only the decisions the user alone can make. It is for them, not the system, and never a substitute for steps 1 to 8.

## The keep test

A fact earns a place in the vault only if it changes what a future session would **do**. Everything else is noise that every later agent pays to read.

Keep it when it is a commitment, constraint, identifier, decision with consequences, or a correction to something the vault already claims. Drop it when it is narration of work already visible in the files or git history, a fact reconstructible in seconds from the code or a note, or something that mattered only inside this conversation.

Two cases deserve an explicit **record nothing**:

- **Borrowed space.** The session used the vault as a workbench for something that is not the user's ongoing work: a favour for someone else, a one-off document, a scratch experiment. Deliver the output, skip the bookkeeping. Ask if unsure; do not default to writing.
- **Tooling changes that document themselves.** A new script command belongs in its tool note and the commit message, not in an effort note or the Agent Log.

When in doubt, prefer one precise line in the right note over a paragraph in a new one.

The [[Maps & Manuals/Agent Log|Agent Log]] has two sections and the keep test applies differently to each. Section 1 takes changes to how the vault itself works, never a record of tasks completed. Section 2 takes this session's mistakes per step 6, and is the one place in the vault that deliberately holds uncertain material: an entry there is a candidate for a rule, not a rule, and it survives only until Weekly Maintenance promotes or discards it.

## Receiving side (mirror rule)

The incoming agent reads the chain (Me, Active Context, effort note) and trusts it over reconstruction, but verifies any load-bearing fact against its source before acting on it or sending it externally.

## Pitfalls seen in practice

- Fixing an error in the drafts but leaving it in the `summary:` field (happened 2026-07-20 in the a bank dispute; caught late).
- Work done outside vault sessions (email exchanges, calls, filings) never logged: the 2026-07-20 session spent hours rebuilding a dispute from 211 emails because two months of developments existed only in a mailbox. After any external development, add a two-line update to the effort note.
- `next:` fields describing themes instead of actions, forcing the next agent to re-derive the plan.
- A parallel session's half-finished work swept into an unrelated commit: on 2026-08-01 two sessions ran at once and one staged broadly, committing the other's in-progress edits to `personal_google.py` under the message "Weekly maintenance 2026-W31". The code was fine; the history lied about who changed what and why. Stage explicit paths.

---

## Related

[[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Active Context|Active Context]] | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Workflows/Weekly Review|Weekly Review]] | [[System/Skills/Tools/Create Vault Skill Note|Create Vault Skill Note]]
