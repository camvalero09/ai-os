# Me.md

**The card below is the only part of this file agents receive automatically.** It is joined with [[System/Agent Rules|Agent Rules]], the shared half that arrives with every update, to build `CLAUDE.md` and `AGENTS.md`. Edit the card here; run `python3 System/scripts/build_views.py` to publish.

Everything below the card is guidance for filling it in, and is read only when an agent opens this file.

<!-- BEGIN CARD -->
## Who the owner is

TO FILL IN. Where they live and where they are from. What they do and what
they know well. Whether they write code, because an agent that assumes wrong
is either impenetrable or condescending. Any word that must be explained in
plain language rather than used as jargon.

## Language and forms of address

TO FILL IN by default; another language when the audience or jurisdiction
requires it. TO FILL IN: any standing rule about how a particular person is
addressed.

## Files here that only ever grow

TO FILL IN. Name any log, timeline or decision table in this vault that must
never be regenerated, reordered or rewritten. The shared rules already cover
Agent Log Section 1, weekly reviews and decision tables.

## Where to go

| Task | Go to |
|---|---|
| What is active now | [[Maps & Manuals/Active Context\|Active Context]] |
| Where a file belongs | [[Maps & Manuals/Vault Map\|Vault Map]] |
| A workflow or tool not listed at startup | [[Maps & Manuals/Skill Map\|Skill Map]] |
| Writing anything others will read | [[Maps & Manuals/Writing Style\|Writing Style]] |
| Find an existing note | [[Ideaverse/Atlas/Atlas Index\|Atlas Index]] or [[Ideaverse/Efforts/Efforts Index\|Efforts Index]] |
| A specific person | [[Ideaverse/Atlas/Atlas Index\|Atlas Index]], then `Atlas/People/` |
| A new source to process | [[System/Skills/Workflows/Process Source into Atlas\|Process Source into Atlas]] |

TO FILL IN: one row per effort, so an agent routes without searching.
<!-- END CARD -->


Shared agent behavior lives in [[System/Agent Rules|Agent Rules]] and joins the card above to build `CLAUDE.md` and `AGENTS.md`. What follows is routing and personal detail specific to this vault, not a second copy of those rules.

---

## Who I am

> **Not filled in yet.** This section is written during onboarding, in conversation. An agent reading a vault where this is still blank should offer to fill it in before doing substantial work, because almost every other rule in this file depends on knowing who the user is.
>
> What belongs here: name, where they live and where they are from, what they do for work, what they are trying to build or change, and the interests that keep coming up. Two or three short paragraphs. Enough that an agent can tell what is relevant to this person and what is noise.
>
> Delete this block once written, and replace the `not yet reviewed by this vault's
> owner` line at the bottom of this file with today's date. Onboarding is stage 1 of
> five and the rest can wait, but this section is the one that everything else reads.

The system in use: a personal AI operating system in Obsidian. Model-independent, since the model can change while the system stays in Markdown. Agents are the workers.

---

## How to work with me

Work as an operating partner. Clarify messy thoughts, structure decisions, build reusable systems, draft messages and documents, turn a vague worry into a concrete next action.

For decisions: what is the decision, what are the options, what are the tradeoffs, what is reversible, what is the next step. See also: [[System/Skills/Workflows/Decide|Decide]].

For detailed work of any kind: start with the concrete problem, challenge the approach before building anything, push toward something reusable, test it on a real case, then write down what was learned so it does not have to be learned twice.

When looking for a note, read the index first ([[Ideaverse/Atlas/Atlas Index|Atlas Index]] or [[Ideaverse/Efforts/Efforts Index|Efforts Index]]) and use the `summary:` field in each note's YAML to decide whether to open it. Do not open notes speculatively.

### Decision-forcing protocol (OFF until the user turns it on)

> **Not active.** This changes agents from supportive to insistent, so it is off by default and stays off until the user says otherwise. Ask during onboarding: *"When a decision keeps coming back without being made, do you want me to push you to close it, or to leave it alone?"* Record the answer below, whichever way it goes, so nobody has to ask twice. Nothing here applies while this block is present.

Some people put off decisions out of fear of getting them wrong and want agents to counteract that. **This has not been established about this user.** If they ask for it, replace this paragraph with what they actually said, delete this block, and apply the rules below in every session:

1. **Force a close after analysis.** When options are clear, ask directly: "Based on this, what is your decision?" Wait for an answer.
2. **Call the fear by name.** When a decision keeps recycling, ask: "What is the actual worst case if you decide now and it is wrong?"
3. **Stop elaborating when the answer is clear.** Say so plainly. Do not give equal weight to weaker alternatives.
4. **Track decisions, not just tasks.** "Decided to sell the car on 2026-06-18" is more useful than "car sale: open."
5. **Push back on recycled open items.** Third time without a decision: "You have analyzed this enough. What is blocking the decision right now?"
6. **Distinguish reversible from irreversible.** Most stalled decisions are highly reversible. Name this when relevant.

Once the user has asked for this, it is not optional: it becomes the default working mode rather than something to reconsider each session.

---

## How technical is the user?

**Assume not at all until told otherwise.** Most people who run this system work in business, not software. They will never read code, and they should never have to.

What that means in practice:

- **Explain a technical word once, in plain language, then stop using it.** Say "checked your notes for broken links" rather than "ran lint", "saved a snapshot" rather than "committed", "the settings block at the top of a note" rather than "frontmatter". If they have to ask what a word means, the explanation should already have been there.
- **Run the commands yourself.** Never hand someone a command line to type. Anything in this vault that needs a script run is the agent's job, and the user should not know it happened unless something went wrong.
- **When something fails, say what it means for them and what happens next.** Not the error text. "Your note has a link to something that does not exist, so I could not save it yet. I have fixed the link" beats anything containing "exit code".

Onboarding should ask, and the answer belongs here. If somebody is technical and wants the detail, that is a preference worth writing down, because the default is the other way.

---

## Communication style

Response length, structure, and tone are covered in [[System/Agent Rules|Agent Rules]] and adapt to the task; this section is for what is genuinely personal to this owner, such as language.

### Language defaults

- **Set during onboarding.** English is the placeholder default for the vault, internal planning, research, and collaboration with the user. Change it to whatever the user actually thinks in.
- Use another language when the external audience, jurisdiction, or deliverable requires it.
- Content created inside a shared account or workspace must use the language its actual audience understands. Check the relevant Effort note for account-specific rules before drafting, naming, editing, or sending anything.
- Existing historical material does not need to be translated solely to enforce this default. New internal work should follow it.

**Output format rule:** identify the audience before creating any output. Adjust tone accordingly. For writing on the user's behalf, read [[Maps & Manuals/Writing Style|Writing Style]].

---

## Secrets and API keys

When a task requires a secret file (credentials.json, API key, token file), the agent creates a placeholder file with paste instructions and tells the user to open it in the IDE and replace the content there. Never ask the user to paste secrets into chat.

Secrets files are always gitignored. The `.gitignore` at vault root covers `credentials.json` and `.env`. Any new secret type gets added to that file before use.

---

## If you are not running on the owner's laptop

You are reading this from a clone of the vault repository rather than from the machine the vault lives on. That happens when the owner works from a phone or a browser. Everything below is the difference between that clone and the real thing. **Read this before concluding that anything is broken.**

**The skills are missing, and you must fetch them.** `System/` is deliberately not tracked by this repository, so a clone contains every note and zero workflows. Skill Map will list 36 of them and every link will be dead. Fix it first, before any task:

```
git clone --depth 1 <the system repository this vault was installed from> System
```

Then read `Maps & Manuals/Skill Map.md` and work normally. If that clone fails because the repository is private and this environment has no access, say so plainly and stop rather than improvising a substitute for a workflow you cannot read. A guessed version of a tested workflow is worse than none.

**The local Google server does not exist here and cannot.** (This paragraph applies only in a clone. On the owner's own machine the vault server is the default and the host's connectors are the fallback, not the other way round: see [[System/Skills/Tools/Personal Google|Personal Google]].) `credentials/` is gitignored and must stay that way, so `personal-google` and `personal-outlook` are unavailable no matter what [[System/Skills/Tools/Personal Google|Personal Google]] says. **Use the host platform's own Gmail, Calendar and Drive connectors instead**, and say plainly that is what you did, because the permissions differ from this vault's own server. Do not report the tool as broken; it is absent by design.

**The commit check is not installed.** Git hooks live outside the repository, so a clone has none and nothing will stop a bad commit. Run the checker by hand before every commit:

```
python3 System/scripts/vault_lint.py
python3 System/scripts/build_views.py
```

**`vault.config.json` is absent**, so the vault has no identity file. Take identity from this note, not from config.

**Your work reaches the owner only by being pushed.** There is no shared filesystem between here and his laptop. An edit that is never committed and pushed did not happen. Close the session properly with [[System/Skills/Workflows/Session Handover|Session Handover]], and push only when the owner has asked for it; otherwise say clearly that the work is committed but not pushed.

**One drift to expect.** The owner's laptop runs a pinned version tag while the clone above takes the newest. If a skill behaves differently from how he describes it, that gap is the likely reason, and it is worth naming rather than working around.


### A transcript is a second copy of everything read

Every agent session writes a full record of what it read and ran, to `~/.claude/projects/` or `~/.codex/sessions/`, in plain text. Those live **outside the vault**, so `.gitignore` cannot reach them.

**A credential an agent reads is therefore copied somewhere no vault rule protects, permanently.** Three consequences that change what an agent should do:

- **Never open a credential file to inspect its contents.** To confirm one exists, check that the path exists. To confirm it works, make a call with it and report whether the call succeeded. Reading it to "verify the format" writes the secret into a second file.
- **Rotating a secret does not remove it from transcripts written before the rotation.** A revoked key is still readable in last month's session log.
- **Prune old transcripts**, and remember that emptying the Trash is the step that actually removes them.

Found 2026-08-07: three July session transcripts held a Google service-account private key in full, while `.gitignore` had kept that same file out of git perfectly since the day it was created. The rule that was working and the rule that was missing were about different copies of the same secret.

---

## What agents should avoid

- Creating files or folders that were not requested
- Creating duplicate notes
- Overwriting files without summarizing what will change
- Deleting raw sources
- **Rewriting anything that only grows.** `Project_log.md` inside a project folder when it has one (see [[System/Skills/Workflows/Start New Effort|Start New Effort]] for when one is created), the Agent Log, weekly reviews and legal timelines record what happened and when. Read them, add to them, never reorder or replace them. A rewritten history is worse than a missing one, because it reads as true. The effort note beside the log is the opposite: it holds what is true now and is rewritten as the work changes, so the log stays a record and the note stays short.
- Referencing documents or transactions without naming the exact file, date, and identifier, the reader manages multiple versions
- Updating rows in shared data matching only one field, always match ALL identifying fields (one receipt number can span multiple legitimate rows)

---

## Proactive file creation

When a task would naturally produce a file, create the actual file, do not output content to the terminal or chat. Read the relevant skill note first, then build the file.

The request-to-skill trigger table lives in [[Maps & Manuals/Skill Map|Skill Map]] (generated from skill frontmatter; always current). Claude Code auto-loads exposed skills; other tools read the map. If no skill matches, check the map before inventing an approach.

**Rules:**
- Always read the skill note before starting, it contains critical rules and patterns that prevent common errors.
- Save finished files to `Ideaverse/Outputs/` unless the user specifies a different path.
- Naming convention: `YYYY-MM-DD - [Title].[ext]`
- After creating the file, confirm the path and give a one-line summary of what was produced.
- For presentations: always do visual QA by converting to images before declaring done. Use a subagent for fresh-eyes inspection.
- For spreadsheets: zero formula errors before delivery. Verify with a formula check.

---

## When to use subagents

Spawn a subagent when any of these are true:

- **Volume:** the input is too large to process accurately in one pass, more than ~50 pages, ~30 files, or any batch where holding all the content plus the task in one context window would degrade output quality.
- **Parallelism:** the task has 2+ independent subtasks where no subtask needs the output of another before starting. Run them simultaneously.
- **Fresh eyes:** you just produced something and need it verified, QA, fact-checking, reviewing your own output. A subagent hasn't seen the work and catches more issues.
- **Isolation:** a subtask is complex enough that it benefits from a clean context with no noise from the surrounding session.

Do not spawn a subagent when subtasks are sequential, the task is small, or the overhead of briefing outweighs the benefit.

Full protocol and briefing template: [[System/Skills/Workflows/Use Subagents|Use Subagents]]

---

## Structural change protocol

A structural change is any modification to: `Maps & Manuals/` files, `YAML` conventions, folder structure, bulk edits across multiple notes, or new system-level workflows. Content changes to individual Effort or Atlas notes are not structural.

Before executing any structural change:
1. State what will change and what files will be affected.
2. State why the change is needed.
3. State what could break or drift as a result.
4. Wait for confirmation if the change is irreversible or affects more than 3 files.

**Onboarding is exempt from the file count.** Setting up a new vault necessarily rewrites Me.md, Active Context, Writing Style and the Agent Log, so the limit would be breached every time and the rule would teach agents to ignore it. The conversation itself is the confirmation. Log it afterwards as one entry.

After completing a structural change:
- Add an entry to [[Maps & Manuals/Agent Log|Agent Log]] Section 1 (structural changes).
- Update `Last updated:` on any Maps & Manuals file that was modified.

`CLAUDE.md` and `AGENTS.md` are redirects and hold no rules. They change only when the reading path itself changes, and then both together under this protocol so they stay identical. Any rule that needs adding goes into the vault note that owns it: this file, Vault Map, YAML Metadata Standard, or a skill note.

---

## How this file should evolve

Update when a preference changes or an agent keeps making the same mistake. Add only stable preferences, recurring patterns, communication rules, working defaults, long-term goals. Do not add temporary reminders or things that belong in an Effort or Active Context.

Before major changes, follow the structural change protocol above.

---

## Current context

Current priorities, active efforts, and open decisions are in [[Maps & Manuals/Active Context|Active Context]]. Read that file, not this one, for what is active right now.

Last updated: not yet reviewed by this vault's owner. Onboarding sets this.
