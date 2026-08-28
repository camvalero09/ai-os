---
id: workflow-onboard
type: workflow
status: stable
domain: ai_os
updated: 2026-08-04
summary: "First-run setup for a new vault: fill in Me.md through conversation, configure identity, connect tools, create the first real effort, and verify the machinery works."
triggers: "onboard, set up my vault, first time, new vault, get me started, /onboard"
expose: true
---

# Workflow: Onboard

Run once, when a vault is new. The person answering owns this vault; you are setting it up with them, not for them.

This vault ships with working machinery and no content. Your job is to turn it into theirs.

---

## Before you start

**Check `onboarding_stage` in `vault.config.json` first.** It holds the number of the last stage that was finished, and it is the only place that knows. `0` means nothing has been done. `2` means resume at Stage 3, and say so out loud rather than starting over: "you got as far as checking the machinery, so next is your first project." `5` means this is finished and you should not be running this workflow at all.

If the field is missing, treat it as `0`, but read [[Maps & Manuals/Me|Me]] before believing that. If its "Who I am" section holds real content rather than the shipped placeholder, someone ran Stage 1 without recording it: set the field to `1` and carry on from there rather than interviewing them a second time.

**Do not do all of this in one sitting.** Stage 1 is a conversation and takes maybe twenty minutes. Stages 3 and 4 involve external accounts and waiting. Tell the person that upfront so they do not feel behind, and tell them the vault is genuinely usable after Stage 2 even if the rest waits a month.

**Write as you go.** Do not conduct a long interview and then produce files at the end. After each answer, write it into the file and say what you wrote. If the session dies halfway, everything before that point survives.

**Set `onboarding_stage` at the end of each stage, before starting the next one.** Not at the end of the session, and not at the end of the workflow. A stage that was finished but never recorded gets done again by the next agent, and the person answers the same questions twice.

**Stopping partway is a normal outcome, not an unfinished job.** When someone runs out of time or interest: record the stage, name the one that comes next in a single sentence, and stop. Do not push to continue.

---

## Stage 1: Who they are

A conversation, not a form. Ask a few questions at a time, follow what they actually say, and skip what does not apply.

1. **Name, where they live, where they are from.** Write into `vault.config.json` (copy `vault.config.example.json` first) and into Me.md's "Who I am".
2. **What they do, and what they are trying to build or change.** This is the most valuable answer in the whole workflow. It is what lets you judge later whether something is relevant to them or noise. Two or three sentences beats a job title.
3. **What they want this system for.** Notes and projects? Managing admin and paperwork? Thinking through decisions? Their answer determines which workflows matter and which are dead weight.
4. **Language.** Which language do they think in? Set `primary_language` in the config and update the Language defaults section in Me.md. Do not assume English because this file is in English.
5. **Timezone.** Into the config. Everything with a date depends on it.

Then replace the placeholder block in Me.md's "Who I am" with what they told you, in their words rather than yours. Delete the placeholder, and replace the `not yet reviewed by this vault's owner` line at the bottom of Me.md, Active Context.md and Vault Map.md with today's date. Those three lines are what the checker compares against `owner_name`, so leaving them in place means the vault claims two different owners at once and agents believe whichever they read first.

### Two things to ask explicitly

**The decision-forcing protocol** in Me.md changes how agents behave, so it should never be applied to someone by default. Explain what it actually does before asking: agents will ask directly for a decision once options are clear, name avoidance out loud when something keeps recycling, refuse to keep presenting weaker alternatives when one answer is obviously better, and push back on the third pass over the same open question. It is useful for someone who overanalyzes and knows it. It reads as nagging to someone who does not. It ships **off**, so describe it, ask, and leave it exactly as it is unless they say yes. Silence and a no both mean off. Note the answer either way, so a future agent does not re-litigate it.

**Writing Style.md** is the voice guide agents read before drafting anything other people will see. It ships empty on purpose: the sections are there, the answers are not. Until it is filled in, agents write plainly and do not imitate anyone, which is the correct default and not a problem to solve today.

Say that it exists and how it gets filled in, then leave it. Two ways, and mention both:

1. **From their sent email**, which is much the better one. It needs Gmail connected first, so it belongs in Stage 4. Flag it now so they know it is coming.
2. **By asking**, which works with nothing connected and is what happens if they never connect email. It can be done any time, in ten minutes, and the file explains how.

Do not fill it in from this conversation. How someone talks to their agent during setup is not how they write to a client.

**Stage 1 done. Set `onboarding_stage` to `1` now.** This is the stage that matters most: everything after it is optional and the vault is already theirs.

---

## Stage 2: Make sure the machinery works

Do this before adding real content, so a broken setup surfaces on a throwaway note rather than on something they care about.

1. **The owner accepts the workspace trust prompt. You cannot do this or verify it.** Ask them to open the vault folder in the editor and click through the prompt once, then confirm they have. Until they do, the permission list is ignored and everything asks for confirmation, which reads as the vault being broken. This catches everyone, so ask rather than assume.
2. `python3 System/scripts/vault_lint.py` should report a clean vault.
3. `python3 System/scripts/build_views.py` should report that views are up to date.
4. Install the commit check if it is not already: `python3 System/scripts/install_hook.py`
5. Confirm the safety check actually blocks a broken note: create one with an invalid `status:`, try to save, confirm it is refused, then delete it. **Run this silently and report only the outcome in one line.** A screen of red error text on somebody's first evening reads as "I have broken it already", not as good news. Worth doing rather than assuming: a hook that silently does not run looks exactly like a hook that passes.
6. Commit. This is their first commit and it should succeed.

**Stage 2 done. Set `onboarding_stage` to `2`.** From here the vault is fully working. If they stop now, nothing is broken and nothing is pending: say that plainly rather than leaving them feeling half set up.

---

## Stage 3: Their first real effort

Not a demo. Ask what is actually on their mind right now, and set that up with [[System/Skills/Workflows/Start New Effort|Start New Effort]].

One real effort teaches more than any explanation, because they see their own situation come back structured. Regenerate views afterwards so it appears in the index tables, and show them that happening: it is the moment the system stops looking like a folder of documents.

Add a routing row to [[Maps & Manuals/Active Context|Active Context]] pointing at it, and fill in Current priorities with the two or three things that genuinely matter now.

**Stage 3 done. Set `onboarding_stage` to `3`.**

---

## Stage 4: Connect their tools

Only what they will actually use. An unused integration is a credential to keep safe for no benefit.

### Gmail and Calendar: use what they already have

**Default: whatever their AI app already offers.** Claude and ChatGPT both connect Gmail, Calendar and Drive with a click, inside the subscription they are already paying for. Turn those on, confirm one read works, and Stage 4 is done.

**Do not set up a Google Cloud project during onboarding.** It was the default here until 2026-08-07 and it was the wrong default: about 45 minutes, a developer console, an OAuth consent screen and a credential file to place by hand. It is the single most likely place for a first evening to collapse, and it buys nothing a new owner can feel on day one.

Note in Active Context which connector they are using, so a later agent does not assume the vault's own server exists.

### The vault's own Google server: optional, later, only if wanted

[[System/Skills/Tools/Personal Google|Personal Google]] is an upgrade, not a step. Offer it only when somebody has used the vault for a while and hits one of the reasons it exists:

- They want the vault to reach Google from a script or an unattended job, which a click-through connector cannot do.
- They want the guarantee that it can never send mail, never delete mail, and never write to Drive, whatever any agent decides.
- They want identical behaviour across agents rather than each vendor's own version.

**If none of those is true for them, they never need it.** Say so plainly rather than leaving it as an unfinished task hanging over the vault.

When somebody does want it, then and only then: their own Google Cloud project and OAuth client, never shared between vaults; `google_account` set in `vault.config.json`, which the tool refuses to run without rather than guessing; the `doctor` command to confirm the connected account is the expected one; and secrets in `credentials/` at the vault root, gitignored, never inside `System/`. Never paste a credential into chat: create the placeholder file and have them paste it into their editor.

### Put the weekly reminder in their calendar

**Do this before leaving Stage 4, using the calendar just connected.** Create a recurring weekly event, about 20 minutes, on a day they choose, titled something like "AI OS: weekly check" with the body: *say `/weekly-maintenance` to your agent*.

This is not housekeeping for its own sake. That weekly run is **the only thing in the entire system that reaches the network to look for an update.** The save-time notice reports versions already downloaded, so with no weekly run the vault never learns a newer one exists and quietly stays on the version it was installed with, forever.

An earlier version of this system ran it automatically on a timer. It needed a Full Disk Access grant, then failed silently for 19 days with nobody noticing, and was deleted. A calendar event they can see is the deliberate replacement: it is either there or obviously not.

If they decline the reminder, say plainly what it costs: no updates and no fixes will ever reach them unless they ask for one by name.

### Writing style from their sent mail

If they chose option 2 in Stage 1, do it now that Gmail is connected.

Search their **sent** messages, not received, since received mail is other people's voice. Ask permission before reading, and ask which kinds of message to look at: work email and messages to family are usually two different voices, and conflating them produces a guide that fits neither.

Read enough to see patterns rather than one-offs: how they open and close, sentence length, formality, whether they hedge or state plainly, recurring phrases, which language they use with whom. Then rewrite Writing Style.md as a description of what you actually observed, with real quoted examples from their own messages.

Two rules. Quote only enough to illustrate a pattern, never whole messages, and never anything sensitive. And describe what they do, not what you think they should do: this file exists so agents can sound like them, which is worthless if it quietly corrects them into someone else.

Anything else they need gets added later, when a task actually calls for it. That is the normal way this vault grows, not a failure of setup.

**Stage 4 done. Set `onboarding_stage` to `4`.** With the click-through connectors this stage is now minutes rather than an evening. If only some tools got connected, record `4` anyway and note which ones are missing in Active Context: a connection added later is a normal task, not unfinished onboarding.

---

## Stage 5: Prove it works

The acceptance test. Start a fresh session, so you are reading the files rather than remembering the conversation, and give the vault a real request in their own words.

A healthy vault will read Me.md and Active Context, route to the right place, respect the frontmatter conventions, refuse to hand-edit generated tables, and produce something that passes lint.

If any of that fails, fix it now. This is the last moment when someone experienced is present.

**Stage 5 done. Set `onboarding_stage` to `5`.** Onboarding is over and this workflow does not run again.

---

## Rules

- Write incrementally. Never conduct the whole interview before creating files.
- Their words, not yours, in Me.md. It is a description of a person, not a summary of an interview.
- Never invent an answer they did not give. Leave it blank and say it is blank.
- Do not fill Ideaverse with examples. Empty folders are correct; fake content is confusing and never gets cleaned up.
- Never ask for a secret in chat.
- Ask before reading their mailbox, every time, even when a previous session was allowed to.
- If they lose interest partway, record `onboarding_stage`, stop, and commit. Stage 1 plus Stage 2 is a working vault. The rest can wait indefinitely and saying so is part of the job.

---

## Related

[[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Vault Map|Vault Map]] | [[Maps & Manuals/Writing Style|Writing Style]] | [[System/Skills/Workflows/Start New Effort|Start New Effort]] | [[System/Skills/Tools/Personal Google|Personal Google]]
