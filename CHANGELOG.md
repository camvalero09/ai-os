# Changelog

What changed in each version of the system, in plain language.

Your agent reads this before asking whether to update. Every entry should make sense to someone who does not write code, because the person deciding whether to accept an update is not a developer.

Versions are git tags. To see which one you have: `git -C System describe --tags`.

**This repository starts at v2.0.** Everything below it, v1.0 to v1.53, was built in a private repository whose commit history carried the author's own name, email, home paths and other personal detail. Publishing that history would have made all of it permanent and public, so the work was moved here as a single clean commit instead. The entries below are kept because they explain why things are the way they are; the commits behind them are not here. **Nothing can be rolled back past v2.0**, since there is no earlier tag in this repository to roll back to.

---

## v2.18 (2026-08-29)

**Fixed**

- **The commit check told you to do the one thing the rules forbid.** When it blocked a commit for out-of-date generated tables, its own advice ended with `git add -A`, which stages everything in the folder including whatever a parallel session has half-finished. That is the exact mistake that put one session's work inside another's commit on 2026-08-01 and again on 2026-08-20. It now says to stage only the files the rebuild reports.

---

## v2.17 (2026-08-29)

**Added**

- **The vault now warns when the always-loaded rules file starts growing back.** Anthropic targets under 200 lines for it and says that past that, agents follow it less. The check warns from 160 lines and never blocks saving, because a check that stops work gets switched off. Currently 114.

**Fixed**

- **The changelog was missing v2.12, v2.13 and v2.14.** Written now from what those versions actually changed.

---

## v2.16 (2026-08-29)

**Changed**

- **Four workflows no longer announce themselves at startup.** Office Hours, Onboard, Start a Tracker and Think Out Loud have been offered in every session since 2026-08-07 and no session has ever reached one, measured with the counter added in v2.15. They still exist and still work; they are now found through the Skill Map, like the document builders and the Delivery Hero workflows. The startup list every agent loads gets about 900 characters shorter. If you find yourself asking for one of these by name and the agent does not know it, that is the cost, and setting `expose: true` on the note reverses it.

---

## v2.15 (2026-08-29)

**Changed**

- **The entry file is now nothing but the rules.** `CLAUDE.md` and `AGENTS.md` used to wrap the rules in a preamble explaining that they were generated, an index of the other Maps & Manuals files, and a "before you start" section. All of it either repeated the rules or had drifted out of date against them, and every session paid for it. Removed: 1,801 characters, about a fifth of the file.
- **Links in the generated entry files are now plain file paths.** `[[Ideaverse/Efforts/Personal Finance/Personal Finance|Personal Finance]]` names the same note twice and an agent cannot open it. It now reads `Ideaverse/Efforts/Personal Finance/Personal Finance.md`. The rules file itself keeps proper wikilinks, so Obsidian is unaffected.
- **"Active efforts" no longer lists finished ones.** Only archived efforts were being hidden, so closed ones sat in a table whose title said they were active.

**Added**

- **A way to see which skills sessions actually use.** `python3 System/scripts/entry_compliance.py --skills` counts, per skill, how many real sessions reached it, across both Claude and Codex. It reads what the tools themselves record, so an agent cannot flatter it. Three filters keep it honest: sessions that wrote a skill note are building it, not using it; a session opening the same note eight or more times is looping on it; and one command naming three or more skill notes is an inventory sweep. Without those, the first run reported a skill as the third most used when 272 of its 284 reads were the six sessions that wrote it.

**Fixed**

- **The compliance check was measuring an obsolete rule.** It asked whether a session read both the rules file and Active Context. Since v2.9 the rules arrive automatically, so reading the rules file is no longer required and counting it understated compliance. It now reports Active Context, which is the file that still depends on the agent choosing to open it.

---

## v2.14 (2026-08-28)

**Changed**

- **The four document builders no longer announce themselves at startup.** Create PDF, Create Presentation, Create Spreadsheet and Create Word Document mostly described things the model already knows how to do. The one part specific to this vault, where a finished file goes and how it is named, is in Create Output, which stays. They remain reachable through the Skill Map.
- **Fifteen skill descriptions rewritten to say what the skill does and stop.**

---

## v2.13 (2026-08-28)

**Changed**

- **The guide for writing a new skill now carries Anthropic's own rules for it.** State what to do rather than narrating why, add only what the model cannot work out for itself, keep the instructions under 500 lines, and treat the summary and trigger lines as the expensive part, because those are loaded into every session under a hard cap. It also now says plainly that making a skill load automatically is a cost decision, not a compliment.

---

## v2.12 (2026-08-28)

**Fixed**

- **The list of skills every agent loads had reached 98% of its limit, and a third of the excess was one repeated phrase.** Every skill's description began with the same 38-character preamble, 1,014 characters in total across the list. Shortened it and trimmed the ten longest trigger lists. Past the limit some skills are simply never offered, and nothing tells you which.

---

## v2.11 (2026-08-28)

**Changed**

- **Rules that only matter sometimes are now skills, so they arrive when they apply instead of on every task.** Handling secrets, changing the vault's own structure, creating a finished file, using subagents, and working from a clone were all sitting in the rules file, loaded into every session whether or not the task went anywhere near them. They are now five skills that load when relevant. This follows both Anthropic's and OpenAI's published guidance: a procedure belongs in a skill, a fact belongs in the always-loaded file.

---

## v2.10 (2026-08-28)

**Changed**

- **The project table on your dashboard no longer repeats every project's whole next step.** It copied each project's next action in full, so the dashboard carried several hundred words that already existed, word for word, one click away in the project note. It now shows the first sentence and links to the rest. The table answers "what is next on each project", not "brief me on everything".

---

## v2.9 (2026-08-28)

**Added**

- **Your rules can now reach every session instead of only the ones that chose to read them.** Your `CLAUDE.md` and `AGENTS.md` told agents to go and read your rules file. Measurement across 149 real sessions on the author's machine found they did that 56% of the time, and only a quarter to a third of the time in short sessions, which are exactly the ones where a quick unconsidered action is most likely. Agents load the entry file on their own, so the rules that matter every time now live in it. They are still written in one place, a section of your own `Me.md` marked as the card, and both entry files are generated from it. Nothing about a rule lives in a file named after a vendor.
- **The skill count in the entry file is now counted, not typed.** It said 36 for months while the real number had moved.

**This does nothing unless you opt in.** If your `Me.md` has no card section, your `CLAUDE.md` and `AGENTS.md` are left exactly as you wrote them and nothing is reported. To adopt it, wrap the rules you want every session to see in `<!-- BEGIN CARD -->` and `<!-- END CARD -->` inside `Me.md`, then run the usual update commands. Ask your agent to do it for you if you would rather not edit by hand.

---

## v2.8 (2026-08-28)

**Fixed**

- **v2.7 blocked saving over a warning, and flagged its own generated files as unlinked notes.** Publishing skills to a second folder made the vault check count those generated pointer files as real notes nobody links to, 21 of them, and the new skill-list notice was filed as a problem rather than a note to yourself, so an 80% reading stopped every save. Both fixed: generated skill folders are ignored the way they always were for Claude's, and the size notice now sits under "worth a look" where it belongs.

---

## v2.7 (2026-08-28)

**Changed**

- **Your skills now reach every agent, not just Claude.** Skills were only ever published where Claude Code looks for them. Codex, which reads a different folder, saw none of them and had to find workflows by reading the skill map by hand every time. In this vault's own measurements Codex ran four out of five sessions. Skills are now published to every agent's folder from the same source note, so both find them the same way and load one only when it is relevant.
- **Skill notes no longer name a vendor.** A note used to say `expose: claude_code`, putting one company's product name inside your own writing. It now says `expose: true`, and which agents receive it is a setting in the generator instead. Older notes saying `claude_code` keep working, so nothing breaks if you have not updated yours. Supporting a new agent is now a single line in one file and no change to any note.
- **A warning before the skill list gets too long.** Agents keep every skill's name and description in mind from the start and pick from that list, and both Anthropic and OpenAI cap it at the same size. Past that cap some skills are simply never offered, and nothing tells you which ones were missed. The vault check now warns at 80% of the limit. This vault is at 84%, so three of the longest descriptions were shortened.

---

## v2.6 (2026-08-28)

**Added**

- **A way to check whether agents actually read your rules before working.** Your `CLAUDE.md` and `AGENTS.md` both tell every agent to read two files before starting anything. Nobody had ever checked whether that happens. `scripts/entry_compliance.py` counts it across both Claude and Codex sessions on your machine, and the first run was not comforting: across 149 real sessions it happened 56% of the time, and in short sessions only a quarter to a third of the time. Short sessions are where a quick unconsidered action is most likely, which is exactly what those rules exist to prevent. The script prints counts only and never reads out transcript content, since those files are known to contain credentials that past sessions opened.

---

## v2.5 (2026-08-28)

**Fixed**

- **The handover report invented a project called "Efforts Index" and asked you to fix it.** It treated the generated index file sitting in the projects folder as though it were a project of its own, then reported two things missing from it that can never be there. Cosmetic, but it put a permanent unfixable task in front of every agent closing a session. Third and last fix to the script released earlier today.

---

## v2.4 (2026-08-28)

**Fixed**

- **The new handover report showed one filename with its first letter missing, and treated auto-generated files as work needing review.** Both were bugs in v2.3, found the first time the script ran for real. Any file starting with a dot, which on this system means anything under `.claude`, lost that dot and would not have matched the file it named. Harmless to read, but a save command built from it would have failed. Fixed the same day.

---

## v2.3 (2026-08-28)

**Changed**

- **Closing a session is cheaper.** Ending a session used to mean the agent rediscovering, by hand, what had changed, which projects those files belonged to, whether the log rows were added and which paths to save. All of that is work a machine can do, and doing it in conversation cost thousands of words of the agent's attention every time. There is now a script, `scripts/handover.py`, that reports it in one step and prints the exact save command. The agent is left with the part that actually needs a mind: rewriting the project note, deciding what is worth keeping, and naming what went wrong.
- **The handover instructions were cut in half above the fold.** The note is now a short set of steps, with the reasoning and the old failures moved below a line marked "stop here in a normal handover". Nothing was deleted; it is just no longer read in full every single time.

**Fixed**

- **Weekly maintenance could commit another session's unfinished work.** The unattended weekly script saved four whole folders at once, so if you or another agent had a file half-written in any of them, it got swept into the weekly save under a message that had nothing to do with it. The history then said the wrong thing about who changed what, which is the one thing a history has to get right. It now saves only the files it produced itself, by name. This is the same rule the written instructions already gave the agent; the script simply had never been held to it.
- **Editing the system from inside a vault used to fail silently.** The `System/` folder is a separate, version-pinned copy that your vault deliberately ignores when saving. So an agent that edited a skill there would be told the session had no changes, save nothing, and lose the work; and because that copy is pinned, saving in place would have left the change stranded where nobody could get it. The handover script now checks for this and says so, pointing at the authoring instructions. Found the hard way while writing this version.

---

## v2.1 (2026-08-20)

**Fixed**

- **Saving could be refused for a history that had lost nothing.** The check that protects your project logs counted the date at the top of the file as a deleted line, so simply touching a log could block the save, and the message claimed a line had been removed when none had. It now ignores the settings block and still refuses any save that really does drop a row. This also restores rollback: v2.0 was the first version here and had nothing behind it to go back to.

---

## v2.0 (2026-08-07)

**Changed**

- **The system is public.** [github.com/camvalero09/ai-os](https://github.com/camvalero09/ai-os). Anyone can install it with one command, no account and no invitation.
- **Published as a new repository rather than by opening the old one.** The files were clean; the years of saved changes behind them were not, carrying the author's name, personal email, home network names, bank, employer and folder paths. Opening the old repository would have made all of that permanent and public, so today's files were published as a single fresh start instead. Nothing secret had ever been saved into it, which was checked first and was the one thing that could not have been undone.
- **Everything below this line happened in the private repository.** The entries are kept because they explain why things work the way they do. The saved changes behind them are not here.

---

## v1.53 (2026-08-07)

**Fixed**

- **A new vault would never have heard about an update.** Only the weekly check looks for one, and nothing was putting that weekly check in anyone's calendar. Setup now creates the reminder while your calendar is being connected, and explains what skipping it costs: no updates and no fixes, ever, unless you ask by name.
- **Silence no longer looks like good news.** If nothing has looked for an update in more than ten days, the vault now says so, instead of leaving "no new version" to mean either "you are current" or "nobody checked".

---

## v1.52 (2026-08-07)

**Fixed**

- **A new vault came with somebody else's reading list.** The starter Atlas index carried the original owner's backlog of notes to write, all from their own profession, so a new owner would open their vault and find a list of unfamiliar subjects waiting for them. It is now empty, with a line explaining what belongs there.

---

## v1.51 (2026-08-07)

**Changed**

- **Setting up Gmail and Calendar is now a click, not an evening.** New vaults connect them through whatever AI app the owner already pays for. The old route, a Google developer account with its own project and a credential file placed by hand, took about 45 minutes and was the most likely place for a first setup to fall apart. It still exists for anyone who wants the vault to reach Google on its own or wants a hard guarantee that it can never send or delete mail, but nobody has to do it, and onboarding no longer leaves it hanging as an unfinished task.

---

## v1.50 (2026-08-07)

**Fixed**

- **Three pieces of one person's life left in the shared system**: a bank named twice in the Outlook tool's trigger phrases, so every adopter's skill list advertised a search for somebody else's bank, the same bank in the session-closing checklist, and the original owner's name in a workflow note. Found by installing the system into an empty folder and searching the result.

---

## v1.49 (2026-08-07)

**Fixed**

- **Your assistants kept using their own Google connection instead of yours.** Nothing had ever told them which to prefer, and their built-in ones announce themselves much more loudly, so they won by default. That mattered: only your own connection checks it is signed in as you, refuses to send mail, keeps Drive read-only, and demands confirmation before changing an event. Yours is now the stated default everywhere, theirs the fallback, and they have to say so when they use theirs instead.

---

## v1.48 (2026-08-07)

**Fixed**

- **A moment of bad wifi shut the whole phone line down.** It waits with the connection open, so a network blip lands mid-request, and one kind of timeout was ending the program instead of being retried. It now waits 30 seconds and carries on, and no network problem of any kind can stop it. If it does stop now, the cause is the laptop itself: asleep, restarted, or out of battery.

---

---

## v1.47 (2026-08-07)

**Fixed**

- **The phone line no longer sends blank messages.** If the assistant returns no text, the conversation now stays quiet instead of showing an empty bubble. The next message continues the same conversation normally.

## v1.46 (2026-08-07)

**Fixed**

- **Codex can now create and change calendar events from your phone.** Calendar writes were waiting for a person at the laptop to approve them, then reporting that the person had cancelled when nobody was there. Those requests now go to Codex's built-in safety reviewer, for both your own Google tools and the Google Calendar connector. The restriction that keeps Codex inside your vault folder stays on.

## v1.45 (2026-08-07)

**Fixed**

- **Corrected advice that was costing time.** The notes recommended Codex for scheduling. It could not create calendar events at all, which is what v1.46 then fixed. Recorded what had been ruled out so nobody investigates it twice.

---

## v1.44 (2026-08-07)

**New**

- **You can now ask which version is answering you.** Send `/version`. It also appears when the phone line starts and every time it updates itself. This exists because a fix can be finished and announced while the laptop is still quietly running the old one, and until now there was no way to tell that apart from the fix not working.

---

## v1.43 (2026-08-07)

**Fixed**

- **Creating or changing a calendar event from your phone did not work.** Reading worked, writing was refused, and the refusal looked like Google turning you away or your login having expired. It was neither: the list of what the assistant is allowed to do named your Google account as a whole rather than each action, and that form quietly permits reading only. Every action is now named. You can create, move, change and cancel events, and draft mail, from your phone.

---

## v1.42 (2026-08-07)

**Changed**

- **Photos and voice notes you send stay on your laptop.** They arrive in your Inbox and are read as before, but they are no longer copied to your online backup, because that copy would be permanent and a picture of a letter or a recording of your voice is the most personal thing here. The trade: those files exist in one place only, so anything worth keeping should be turned into a note. PDFs and documents are still backed up.

---

## v1.41 (2026-08-07)

**New**

- **A rule about where your secrets actually end up.** Every AI session writes a full record of what it read, in plain text, in a folder outside your notes that your ignore-list cannot protect. So a password file an agent opens gets copied somewhere permanent. Agents are now told never to open a credential to look inside it, and to check that it works instead. Weekly maintenance now measures those folders and clears out finished months.

**Fixed**

- **A changelog entry that described the wrong thing.** v1.25 read as though the weekly comparison against GitHub had been removed. It had not, and it still runs; what went was a copy of it running unattended on GitHub's servers.

---

## v1.40 (2026-08-07)

**Fixed**

- **The phone had no memory, despite the feature being there.** Every incoming message overwrote the record of your open conversation before reading it, so each one started from nothing. The conversation was being saved correctly and thrown away one message later. Follow-up questions work now.

---

## v1.39 (2026-08-07)

**Changed**

- **The phone line picks up updates on its own.** Until now, every improvement meant going to the laptop and restarting it by hand, and forgetting meant quietly using the old version. It now notices its own code changed and reloads between messages, so nothing is interrupted. `/restart` still does it manually.

---

## v1.38 (2026-08-07)

**New**

- **Talk to your vault instead of typing.** Send a voice note and it is turned into words on your own laptop, shown back to you so you can see what it heard, then answered. Nothing is uploaded and it costs nothing per use, so you can dictate anywhere. Needs a one-time setup of two tools and a 141MB language file; the note has the three commands. Without them, voice notes are still saved and it tells you why it could not listen.

---

## v1.37 (2026-08-07)

**New**

- **Send photos and files from your phone.** They land in your Inbox with the date on them, and the agent reads them and answers. Add a caption to say what you want done. A photo of a letter, a PDF, a spreadsheet all work.
- **Voice notes are saved but not understood.** Nothing on the laptop can turn speech into text yet, so it says so plainly instead of failing quietly. Adding it means installing transcription software, which is a real change and is left as your decision.

---

## v1.36 (2026-08-07)

**Changed**

- **Your phone now uses the fast model by default**, because a phone question is usually "what is on Thursday" rather than a piece of real work. The same calendar question came back in 18 seconds instead of 27. Your laptop is unaffected: this applies only to messages arriving over Telegram.

**New**

- **`/model` changes which model answers**, from the phone. `/model sonnet` for something that deserves more thought, `/model default` to go back to fast. A name that does not exist is tried and refused rather than saved, so a typo cannot leave your phone line broken.
- **Claude can now use your own Google account tools**, the same ones Codex uses, after one setup command written into the note. Before this it could only reach the host's calendar connector, and none of your own mail.

---

## v1.35 (2026-08-07)

**Fixed**

- **Claude could not see your calendar from your phone; Codex could.** That looked like a difference between the two AIs and was a spelling mistake: they reach Google by different routes and only one route was listed as permitted. Both now read and write your calendar from the phone. The note also says which one to use for what.

---

## v1.34 (2026-08-07)

**New**

- **Your phone conversation now has a memory.** Ask a follow-up without repeating what you were talking about. The thread stays open for three hours of quiet and then starts fresh on its own, so it never drags this morning into tonight. `/new` clears it straight away when you change subject. Each AI keeps its own thread, so switching between them does not mix them up.

---

## v1.33 (2026-08-07)

**New**

- **Switch which AI answers, from your phone.** Send `/agent` to see who is answering and `/agent codex` or `/agent claude` to change it. It takes effect on your next message and is remembered, so a restart keeps your choice. No editing files.

---

## v1.32 (2026-08-07)

**New**

- **You can choose which AI answers your phone.** Claude or Codex, set with one line in your settings file. Both were tested on the same question and gave the same answer; Codex was faster. Claude stays the default because it can be limited more precisely: it is given a list of exactly what it may do, where Codex is instead confined to your vault folder but can run anything inside it. The note explains the trade so the choice is a decision rather than an accident.

---

## v1.31 (2026-08-07)

**Fixed**

- **Answers on your phone are now written for a phone.** The agent had no idea where its reply was going, so it followed your vault's writing rules, which are written for a laptop screen, and sent back headings and tables that arrive as stray `##` and `**` characters. It is now told the answer is going to a phone: plain text, a few short lines, answer first.

---

## v1.30 (2026-08-07)

**Changed**

- **The phone line shows "typing..." while it works**, instead of replying "Working on it" and leaving that line sitting in the chat forever. It looks like a person thinking, which is what it is doing.

---

## v1.29 (2026-08-07)

**Fixed**

- **The command to start the phone line now includes the folder to run it from.** Without it you get "can't open file", which looks like the program is missing when it is simply in another folder. Also notes that only one copy may run at a time.

---

## v1.28 (2026-08-07)

**Fixed**

- **The instructions for keeping the laptop awake were wrong.** They gave one setting where two are needed, and said the lid could be closed. Closing the lid is a separate kind of sleep that no setting reliably overrides. What works is leaving the lid open with the screen locked, or attaching an external display.

---

## v1.27 (2026-08-07)

**Fixed**

- **The phone line could not actually reach the agent.** Two faults, both found by testing it rather than reading documentation: your message was being absorbed by the settings that limit what the agent may touch, so it arrived empty, and the agent could pick up stray text from the terminal and answer that instead of you. Both are closed. v1.26 does not work; take this one.

---

## v1.26 (2026-08-07)

**New**

- **Talk to your vault from your phone, over Telegram.** Your laptop stays awake with the lid closed and answers from your pocket, with the same agent you get at the keyboard: it reads and writes your notes, reads your mail and calendar, and saves its work. Only your own Telegram account can reach it, and it refuses to start if that list is empty. It will not delete anything, undo history, or install anything from the phone. Setup is in the new Telegram Remote note and takes about ten minutes.
- **Agents working from a copy of your vault now know what is missing.** If you ever open your notes somewhere other than your own laptop, the agent is told to fetch the skills itself, to use that platform's own mail and calendar rather than reporting yours as broken, and to run the checks by hand since they only run automatically at home.

---

## v1.25 (2026-08-07)

**Removed**

- **The automatic check that ran on GitHub after every save.** (Corrected 2026-08-07: this entry first read as though the weekly comparison itself was removed. It was not, and it is still part of weekly maintenance. What went was the copy that ran on GitHub's servers unattended.) It guarded against an agent quietly rewriting the record, which has never happened; the failure that has happened is carelessness, which the free check at save time already catches. It also printed removed lines into a log that lives forever, which is the wrong place for them.

---

## v1.24 (2026-08-06)

**Changed**

- **Stronger protection for the files that only ever grow.** Briefly, the system tried to enforce this from outside your laptop as well. Reversed the next day: see v1.25.

---

## v1.23 (2026-08-06)

**Fixed**

- **The "stuck on" column landed on the wrong page** in v1.22. It was added to the project index instead of your list of active projects, which is where you actually read it.

---

## v1.22 (2026-08-06)

**Changed**

- **Your list of active projects now shows what each one is stuck on**, and how many questions it is still carrying, instead of repeating the project's goal back at you. One line per project, which is the view you actually want when you ask "where is everything".
- **Closing a session is ten steps again**, not twelve, with the four new ones absorbed. Refreshing the settings block is part of rewriting a note rather than a step of its own, and getting deadlines out of the chat is part of sweeping it.

**New**

- **A question open for more than 30 days gets flagged**, so a forgotten one surfaces instead of quietly aging. It appears when you check the vault, never raised at you mid-conversation.

---

## v1.21 (2026-08-06)

**Fixed**

- **The new history check refused a legitimate repair.** When a file moves, links pointing at it have to be updated or they break, and the check read that as rewriting the entry. It now compares the words and ignores link targets.

---

## v1.20 (2026-08-06)

**Changed**

- **A project is now a folder, not a file.** The project note holds only what is true now and is rewritten freely, so it stays readable in one screen. What happened and when moves to `Project_log.md` beside it, which only ever grows. One project note had reached 441 lines and no agent could say where it stood without reading it backwards.
- **Finished work lives inside the project that produced it.** Outputs used to sit in one flat folder with no connection to the work they came from, so three verdicts written on the same day sat unread because nothing pointed at them. Each project now lists its own outputs, and the shared index still shows everything in one place.
- **Outputs carry a one-line description.** The index used to list filenames and nothing else.

**New**

- **The vault now refuses to save a history that lost a line.** The rule against rewriting a record has existed since 2 August and was enforced by nothing; two days later an agent rewrote 33 past entries into folder names that did not exist when they were written. Checked mechanically now.
- **Closing a session updates the project, not just the log.** Four steps added: rewrite what is true, add one dated line naming which agent did the work, write the answer into any question the session settled, and file outputs where the project can find them.

---

## v1.19 (2026-08-05)

**New**

- **A way to think with your agent where nothing gets written.** Every other workflow here produces a note, a decision or a file, so every conversation bends toward producing something and a half-finished idea gets tidied into a heading before it is ready. This one's output is deliberately nothing. Say "think out loud with me" and it stays a conversation until you decide something is worth keeping.

**Changed**

- **Replies are now written to be skimmed.** Short paragraphs, a header or a list every few lines, bold lead-ins on bullets, and the thing being asked of you on its own line at the end. The test is that reading only the bold text and headers should tell you what the message says.

---

## v1.18 (2026-08-05)

**Changed**

- **The workflow list is announced rather than loaded.** v1.17 made agents read the whole Skill Map before every task, which worked but cost about 130 lines of reading in every session forever. The entry files now just say the list exists and how many things are on it, which is the one fact an agent cannot work out for itself, and let it go and look when that is relevant. Cheaper, and it should do the same job.

---

## v1.17 (2026-08-05)

**Changed**

- **Agents now read the Skill Map before deciding how to do something**, instead of only when they think they need it. Tested with the OpenAI desktop app: it followed every rule in your vault correctly and never once looked at the list of workflows, so it invented its own approach to a job the vault already had a tested way of doing. In the Anthropic app the skills load by themselves and this was invisible. Everywhere else, the whole skills layer was dead weight.
- **Every save now records which agent made it.** More than one kind of agent works in a vault, and they all save under the owner's name, so the history could not say who changed what. A one-line marker at the end of each save fixes that.

**New**

- **What to do when two apps are open at once.** They share one connection to your Google account, and when one refreshes it the other stops working, with an unhelpful error. Nothing is broken and nothing needs reauthorizing: restart the app that failed. This is now written down, along with the instruction never to fix it by making a second connection.

---

## v1.16 (2026-08-04)

**New**

- **The vault now refuses to keep an instruction file it did not expect.** Agents read files like `CLAUDE.md` and `AGENTS.md` as rules, and most of them read ones sitting in subfolders too. So a file with one of those names, arriving in a download or a shared folder, quietly becomes rules nobody wrote. Saving is now blocked until it is gone. Only the two at the top of your vault are meant to exist.
- **Permissions you granted by clicking "always allow" are now visible.** They used to be invisible forever after the moment you clicked. Every save now lists them once, with how to take them back.
- **Setting up your vault can stop halfway.** It is five stages over several evenings, and there is now a proper record of where you got to, so the next session picks up instead of starting again. Stopping after stage two leaves you with a complete, working vault, and it now says so.

**Fixed**

- **Your vault could claim two different owners at once.** Your name could be filled in on one side while the main files still said nobody had reviewed them. Agents believed whichever they happened to read first. This is now reported.
- **Setting up a tracker no longer stalls on five questions.** If you are not there to answer, it uses sensible defaults, builds the thing, and tells you in one line what it assumed.
- **Onboarding described a writing guide that no longer exists in that form.** It offered to keep the previous owner's voice, which v1.15 removed.
- **The installer no longer ends with a line that looks like a crash** when the version cannot be read.

---

## v1.15 (2026-08-04)

**Fixed**

- **The writing guide shipped carrying one person's voice, name and habits.** It had the system author's surname in its title and instructions to write the way they write. Every message an agent drafts is routed through that file, so it was being used. It now ships empty: the questions, none of the answers. Until you fill it in, agents write plainly and do not imitate anyone.
- **A broken settings block at the top of a note was invisible.** The check that reads settings only looked in two folders, so a note anywhere else could be broken and still be reported clean. That is how the above shipped. Every note is checked now.
- **The system claimed you avoid decisions out of fear.** It was written about the author and applied to everyone. It ships off, and onboarding asks before switching it on.
- **Plainer language** in the vault map, the entry-point files and the project template, which opened with jargon.

---

## v1.14 (2026-08-04)

**Fixed**

- Today's date came from several places that could disagree. One home now.
- Running a script from the wrong folder gives a message that says which folder to use.

---

## v1.13 (2026-08-04)

**Fixed**

- A second fresh-eyes review of the whole system: eleven fixes, mostly instructions that assumed the reader writes code.

---

## v1.12 (2026-08-04)

**Fixed**

- **The "an update is waiting" notice could never appear.** It only looked at what had already been downloaded, and nothing ever downloaded. Weekly maintenance now checks.

---

## v1.11 (2026-08-04)

**Fixed**

- Setup steps that the split into two folders had broken.
- A vault nobody has set up yet now says so, instead of quietly behaving as though it knows you.

---

## v1.10 (2026-08-04)

**Fixed**

- The path a brand new person actually walks, end to end.

---

## v1.9 (2026-08-04)

**Changed**

- **The vault check now speaks plainly.** It used to report things like "unescaped pipe in table wikilink" and "entry-point drift", which tell you nothing you can act on unless you wrote the checker. Each problem is now named for what it means and followed by how to fix it, and passing checks are counted instead of listed, because a wall of OK trains you to skim past the one failure.

**New**

- **The vault tells you when an update is waiting.** If a newer version has been downloaded, it says so every time you save, in one line, with what to ask for. You never have to remember to check. It reads only what is already on your machine, so it never slows saving down and works offline.

---

## v1.8 (2026-08-04)

**Fixed**

- A link added in v1.7 used the old pre-split path and did not resolve. Caught by the vault checker, which is what it is for.

---

## v1.7 (2026-08-04)

**New**

- **One-command install.** `python3 System/scripts/install_vault.py` turns an empty folder into a working vault: your own notes seeded, settings written, credential folders created, git started, commit check installed, tables generated, checker run. It refuses to run where a vault already exists.
- **An acceptance test.** `python3 System/scripts/acceptance_test.py` answers a question the checker does not: would an agent that has never seen this vault find its way. Eighteen checks on the entry point, the reading path, routing, the skills an agent is told about, and whether secrets are about to be committed. It ends by describing the one step only a person can do.
- **The second-time rule** is now written down in Create Vault Skill Note: the second time something is handled ad hoc, offer to save it as a workflow. Not the first, not the fifth, and a no is a normal answer.

**Changed**

- Both setup guides now describe installing from GitHub. The old routine of tarring a folder and transferring it by AirDrop or zip is gone, along with the symlink that used to go missing in transit.

---

## v1.6 (2026-08-04)

**Fixed**

- A new vault's Skill Map arrived with a leftover section named after one person's former employer, visible until the first regeneration.

---

## v1.5 (2026-08-04)

**Fixed**

- Found in a security review: the Gmail tool's instructions to agents still named one specific organization, so every adopter's agent would have been told a rule about somebody else's mailbox. Now stated generally.

---

## v1.4 (2026-08-04)

**New**

- The Update System note now documents how the person who maintains the system actually changes it: work in a separate copy, never inside a vault's `System/` folder, and commit, tag and push all three or the change reaches nobody. Also states plainly that a published version is never moved, only replaced by a new one.

---

## v1.3 (2026-08-04)

**New**

- Your vault now tells you when system work is stranded, every time you save. Three cases it catches: a change made inside `System/`, which is a read-only copy so the change reaches nobody; work committed in the authoring copy but never pushed; and work pushed without a new version tag, which vaults cannot install because they move by tag.
- Set `system_authoring_path` in `vault.config.json` to the folder where you write system changes. Leave it unset if you do not author the system, and nothing extra is checked.

These are warnings, never blocks. Stranded work is a mistake, not a broken vault.

---

## v1.2 (2026-08-04)

**Fixed**

- The Outlook tool could not start. It uses a different path library from the other scripts, and the shared path helper was wired into it with the wrong one.

---

## v1.1 (2026-08-04)

**Fixed**

- The `Private/` folder is no longer reported as an unlinked note. Nothing is allowed to link to it on purpose: a link there would let an agent follow it and turn one session's private observation into vault fact. One vault had this rule and the shared system did not.

---

## v1.0 (2026-08-04)

The first version where the system is separate from anyone's personal notes.

Before this, the system and one person's notes lived in the same place, so improvements had to be copied by hand into every vault and drifted apart within days. Now there is one system that every vault installs, and updates arrive as a version you can accept or decline.

**What is in it**

- 32 skills: workflows for capturing notes, processing sources, making decisions, pressure-testing an idea, closing a session, and weekly upkeep, plus tools for documents, spreadsheets, presentations, PDFs, Gmail, Calendar, Drive, Outlook, and the Discord support channel.
- A link and format checker that runs before every save and blocks broken links.
- Generated index tables, so no one hand-maintains a list of their own notes.
- A safety check that asks before any command that could destroy something.
- Setup guides for Mac and Windows, and a guided onboarding conversation.

**New in this version**

- Gmail attachments can be downloaded, by name or by attachment id. Downloads never overwrite a file that already exists.
- Two new workflows: **Roast**, which convenes five personas to attack an idea and returns one verdict, and **Office Hours**, which questions the founder rather than the idea.
- The Skill Map now separates shared skills from your own, so it is always clear which ones travel to other people and which stay with you.
- The safety check that asks before destructive commands now ships to everyone. It used to exist in only one vault.

**Fixed**

- The system no longer contains any one person's name, email address, or machine paths. An earlier copy still told new users to sign in with someone else's Google account in six places, and carried that person's folder paths in three files.
- The scripts no longer assume the system and the notes live in the same folder.
