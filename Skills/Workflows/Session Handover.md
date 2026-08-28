---
id: session-handover
type: workflow
status: stable
domain: ai_os
updated: 2026-08-28
summary: "Close a session so the next agent can act without seeing the conversation. Run System/scripts/handover.py, then do the judgement steps it lists."
triggers: "wrap up, close the session, handover, hand over, let's finish for today, pick up tomorrow, end of session"
expose: true
---

# Session Handover

Chat history dies with the session. The vault is the handover.

## Start here

```
python3 System/scripts/handover.py
```

It reports what changed, which efforts those files belong to, which steps are already done, and the exact commit command. **Do what it says, then run it again until the checks pass.** Everything below the fold in this note is background; you do not need it for a normal handover.

The script does the checkable half. The half it cannot do is the reason this workflow exists:

- **Rewriting each effort note to say what is true now.** Replace, do not append. If it cannot be read in one screen it has failed.
- **The fact sweep.** Anything said only in the conversation is a candidate. Then apply the keep test below.
- **Naming this session's mistakes.**
- **One observation in `Private/Outside View.md`.**

## The one test

Could a fresh agent, reading only [[Maps & Manuals/Me|Me]], [[Maps & Manuals/Active Context|Active Context]] and the effort note, continue this work without mistakes? If anything needed to pass that test exists only in the conversation, the handover is not done.

## The keep test

A fact earns a place in the vault only if it changes what a future session would **do**. Everything else is noise every later agent pays to read.

**Keep** commitments, constraints, identifiers, decisions with consequences, and corrections to something the vault already claims. **Drop** narration of work the files or git history already show, anything reconstructible in seconds, and anything that mattered only inside this conversation.

Two cases deserve an explicit **record nothing**:

- **Borrowed space.** The vault was a workbench for something that is not Camilo's ongoing work: a favour, a one-off document, a scratch experiment. Deliver the output, skip the bookkeeping.
- **Tooling that documents itself.** A new script command belongs in its tool note and the commit message, not in an effort note or the Agent Log.

When in doubt, one precise line in the right note beats a paragraph in a new one.

## Facts carry identifiers

"The ticket from earlier" dies with the session. "Ticket 46903162214, due 2026-08-11" survives. Numbers, radicados, dates, amounts, file paths, email subjects.

Separate four states explicitly: what **happened** (with evidence), what was **decided** (by whom), what is **pending** (owner plus deadline), what is **blocked** (on what, until when). Blurring pending and blocked makes the next agent re-analyse instead of act.

Record **verification status**, not just conclusions. "Proven from the source document" and "Camilo recalls, unverified" get different markers. Unverified claims that reach external documents are how sessions ship errors.

---

# Background

**Stop here in a normal handover.** Below is why the steps exist and how they have failed before. Read it when a step does not fit, when the script flags something you do not understand, or when changing this workflow.

## Why each step is there

1. **Write to where the next agent will look.** The reading path is Me, then Active Context, then the effort note. A summary in the chat's final message is a handover to the user, not to the system.
2. **Corrections propagate everywhere.** When a fact you wrote earlier turns out wrong, hunt down every copy: body text, drafts, and especially the frontmatter `summary:`, because that is what agents read to decide whether to open the note. A stale confident claim is worse than a missing one.
3. **A question leaves the open list by having its answer written into the row**, never by being deleted. Skipping this is why a resolved contract question sat listed as blocking for two days.
4. **Outputs need a real `summary:`.** A generated table can list a file; it cannot know what the file decided. If it concluded something, write the conclusion into the effort note too.
5. **`next:` is a concrete dated action** ("file SFC queja 2026-08-12 15:00 Berlin"), never "continue the work".
6. **Deadlines get externalised**, as a calendar event via [[System/Skills/Tools/Personal Google|Personal Google]] for time-critical ones and an explicit date in `next:` otherwise. A deadline buried in prose is a missed deadline.
7. **The Agent Log has two sections and the keep test applies differently to each.** Section 1 takes changes to how the vault itself works, never a record of tasks completed. Section 2 takes this session's mistakes, in the format `YYYY-MM-DD | what went wrong | fix applied or rule to add`, and is the one place in the vault that deliberately holds uncertain material: an entry there is a candidate for a rule, not a rule, and it survives only until [[System/Skills/Workflows/Weekly Maintenance|Weekly Maintenance]] promotes or discards it. Log a mistake if it cost real time, sent the session down a wrong path, or would have been avoided by a rule that does not exist yet. Not typos, not one-off tool errors. An empty session is fine, but say so rather than skipping silently.
8. **Outside View has its own rules; read its header before writing there the first time.** Insert directly under the marker and do not read the entries below it: independent reads are the entire point, and an agent that reads last month's entry writes an agreement with it. Observations only, never advice, one or two at most. "Nothing new this session" is valid and is the most common entry. Nothing recorded there may be quoted back to Camilo in session or used to decide anything.
9. **Commit explicit paths.** Never `git add -A` or a directory you did not touch. The script prints the command with `-o`, which commits only the named paths and ignores whatever else is sitting in a shared index. If `git status` shows changes you did not make, another session is probably live: leave them and name them in the wrap-up.

## Pitfalls seen in practice

- Fixing an error in the drafts but leaving it in the `summary:` field (2026-07-20, a bank dispute; caught late).
- Work done outside vault sessions (email exchanges, calls, filings) never logged: the 2026-07-20 session spent hours rebuilding a dispute from 211 emails because two months of developments existed only in a mailbox. After any external development, add a two-line update to the effort note.
- `next:` fields describing themes instead of actions, forcing the next agent to re-derive the plan.
- A parallel session's half-finished work swept into an unrelated commit: on 2026-08-01 two sessions ran at once and one staged broadly, committing the other's in-progress edits under the message "Weekly maintenance 2026-W31". On 2026-08-20 it happened again in the seconds between verifying the staged set and committing. The code was fine; the history lied about who changed what and why.
- Reading this whole note every time. It was 1,538 words and all of it was loaded on every close, including the pitfalls, which are only useful when something breaks. That is what the fold above is for.

## Receiving side (mirror rule)

The incoming agent reads the chain (Me, Active Context, effort note) and trusts it over reconstruction, but verifies any load-bearing fact against its source before acting on it or sending it externally.

---

## Related

[[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Active Context|Active Context]] | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Workflows/Weekly Review|Weekly Review]] | [[System/Skills/Tools/Create Vault Skill Note|Create Vault Skill Note]]
