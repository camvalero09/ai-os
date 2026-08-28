---
id: tool-telegram-remote
type: tool
status: draft
domain: ai_os
updated: 2026-08-07
summary: "Talk to the vault from a phone over Telegram, with the full agent behind it rather than a fixed menu. Requires the laptop awake and an allowlist of exactly the owner's Telegram ID."
triggers: "telegram, from my phone, on the go, remote, message the vault, phone line, away from the laptop"
expose: true
---

# Telegram Remote

Message your bot, the agent works in your vault on the laptop, the answer comes back to your phone. Same agent you get at the keyboard: it can read and write notes, search the web, read your mail and calendar, and commit its work.

**The laptop must be awake and on power.** This is not a cloud service and there is no second machine. See "Keeping the laptop awake" below, because closing the lid is not the same as leaving it idle and the difference is easy to get wrong.

---

## What this is not

[[System/Skills/Tools/Discord Bridge|Discord Bridge]] and its remote are a **fixed menu with no model in the loop**: status, next, note, search. That design exists because a Discord channel is something other people can write into, so any message might be from anyone.

This is the opposite trade. One allowlisted sender, full agent behind it. Use the Discord remote when the channel is shared. Use this when the channel is yours alone.

---

## The one control everything rests on

**Every message is checked against `telegram_allowed_ids` in `vault.config.json` before anything reads it.** A message from any other ID is logged and dropped with no reply, so an unknown sender learns nothing, not even that this exists.

It fails closed. An empty or missing allowlist accepts nobody and the script refuses to start.

That single check is what makes a general agent acceptable here at all. **Do not add a second person to that list.** If someone else needs a phone line into a vault, they need their own vault, not a seat in this one.

Second layer, not the wall:

- The agent runs with an explicit tool allowlist, not with permissions disabled. It edits, reads mail and commits. It does not delete, force push, or install.
- A refusal list blocks `rm`, `git reset --hard`, `git push --force`, `--no-verify`, `sudo`, package installs and `curl` before the agent ever sees the message.
- Every message in and reply out is appended to `logs/telegram_remote.log`.
- The vault is a git repository and the agent commits, so anything written from the phone can be undone at the laptop.

---

## Setup, once

**1. Make the bot.** In Telegram, message `@BotFather`, send `/newbot`, pick a name. It replies with a token.

**2. Save the token.** Paste it into `credentials/telegram_bot_token.json.key`, replacing the placeholder. That folder is gitignored and the file is never printed, not even in an error. Never paste a token into a chat with an agent.

```json
{ "token": "1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
```

**3. Install the agent CLI**, once, if `claude --version` does not answer:

```
npm install -g @anthropic-ai/claude-code
```

Then run `claude` once in a terminal and sign in. The bridge cannot sign in for you.

**4. Find your Telegram ID.**

```
python3 System/scripts/telegram_remote.py --pair
```

Message your bot from your phone. The terminal prints your ID and replies to nobody. Ctrl-C when you have it.

**5. Put the ID in `vault.config.json`:**

```json
{ "telegram_allowed_ids": [123456789] }
```

---

## Running it

Open Terminal and paste this in one go, including the `cd`. A vault path usually
contains spaces, so the quotes are not optional:

```
cd "/path/to/your/vault" && caffeinate -is python3 System/scripts/telegram_remote.py
```

Pasting only the second half runs it from your home folder and fails with
`can't open file`, which reads like the script is missing when it is not.

You should see three lines ending in `listening. 1 allowed sender(s).`

**In a visible terminal, never as a background job.** This vault once ran upkeep from a launchd job that died silently for nineteen days because nothing was watching; a window printing a heartbeat is either there or obviously gone.

Send `/stop` from the phone to end it. Ctrl-C at the laptop does the same.

**Only one copy may run at a time.** Telegram allows a single poller per bot, so
a second one fights the first and messages land unpredictably. If replies stop
or arrive twice, check for a stray copy with `pgrep -fl telegram_remote.py`.

### When the network drops

It keeps the connection to Telegram open for 25 seconds at a time waiting for a message, so a moment of bad wifi lands right in the middle of a request. That is normal and expected: it logs a line, waits 30 seconds and carries on.

**Nothing about the network ends the process.** Timeouts, refused connections, DNS, a dropped route, a truncated reply. If the terminal window is still open, it is still trying.

If it does stop, the window will be gone or show a traceback, and the cause is on this machine rather than out there: the laptop slept, was restarted, or ran out of battery.

### Knowing which build is answering

`/version` from the phone, and the same line is printed at startup and after every reload:

```
system: v1.43  (/path/to/vault/System/scripts/telegram_remote.py)
```

It exists because of a specific failure, twice on 2026-08-07: a fix was written, tested and announced against the authoring copy of the system while this machine kept running the old one. The behaviour looked identical to the bug being unfixed.

**If a fix was announced in some version and `/version` shows an older one, the laptop has not picked it up.** That is the first thing to check before assuming a fix did not work.

### Updates apply themselves

Updating the system checks out a new version of this script underneath a process that is already running, which would otherwise keep serving the old code until somebody remembered to restart it.

**It watches its own file and reloads when it changes**, between messages so a reload can never interrupt work in progress. The terminal window stays as it is; you will see one line saying it reloaded. `/restart` does it by hand if needed.

So after `git -C System checkout v1.x`, do nothing. The next message is answered by the new version.

### Keeping the laptop awake

Both flags are needed and they do different jobs. `-i` prevents *idle* sleep. `-s` prevents *system* sleep while on AC power. An earlier version of this note gave only `-i`, which leaves the machine free to sleep anyway.

| What the owner does | Still answering |
|---|---|
| Locks the screen | **Yes.** A lock screen does not stop processes |
| Leaves the lid open, display sleeps | **Yes** |
| Closes the lid | **Probably not**, unless an external display is attached |

Closing the lid is a separate sleep trigger from going idle, and no `caffeinate` flag reliably overrides it. The two arrangements that do work are an external display attached on power, which is the documented clamshell mode, or simply leaving the lid open with the screen locked.

Worth checking the machine's own settings once, because an aggressive default makes this much harder than it looks:

```
pmset -g | grep -E "^ sleep|displaysleep"
```

On the vault where this was built, AC sleep was set to one minute.

---

## Which one for what

Both read and write your calendar, both read your notes. They get to Google by different roads, and that decides the recommendation more than the models do.

| | Claude | Codex |
|---|---|---|
| Google route | this vault's `personal-google` server, once registered with `claude mcp add` | this vault's `personal-google` server |
| Calendar | yes | yes |
| Gmail | yes, through the same server | yes |
| Speed | slower | faster |
| Containment | per tool, tighter | per directory, looser |

**Either, now.** The Claude CLI does not load this vault's Google server on its own, which is why Claude could once read no calendar while Codex could. Register it once and the difference disappears:

```
claude mcp add personal-google -s local -- /path/to/node "<vault>/System/scripts/personal_google_mcp.mjs"
```

Run that from the vault folder. `-s local` keeps it to this project and out of any shared file. Confirm with `claude mcp list`.

**For anything that rewrites notes, Claude.** Its restriction is a list of exactly what it may touch, which is what you want when the work is inside the vault rather than inside your calendar.

Neither answer is about the model being cleverer. It is about which door each one has a key to.

### Resolved in v1.46: Codex calendar writes

The call was reaching the right tool and Google account. The refusal came from Codex's own approval layer: calendar creation is marked as a write, the default reviewer is `user`, and a headless `codex exec` has no person present to approve it. The unanswered approval was reported misleadingly as `user cancelled MCP tool call`.

`approval_policy = "never"` does not mean approve everything. In a non-interactive run it rejects anything that still needs approval. Changing one server's `default_tools_approval_mode` also does not cover the curated Google Calendar app.

The bridge now passes this setting on both a new conversation and a resumed one:

```text
approvals_reviewer="auto_review"
```

That sends eligible write approvals from both the vault's `personal-google` MCP server and the curated `google_calendar` app to Codex's built-in safety reviewer instead of waiting for a person. It changes who reviews the request, not what Codex can reach: `--sandbox workspace-write` remains in force, and resumed conversations carry the equivalent `sandbox_mode="workspace-write"` setting.

---

## Photos and files

Send one and it lands in `Ideaverse/Inbox/`, named with the date, and the agent reads it. Add a caption to say what you want done; without one it is asked to say what the file is and what to do with it.

It goes to the inbox rather than a temp folder deliberately. A photo of a letter is usually something to deal with later, and a file read once and thrown away cannot be looked at again.

**Photos, recordings and video in the Inbox are not backed up**, by design. `.gitignore` keeps them off the remote, because git history is permanent and a dictated voice note is among the most personal things this vault holds. They exist only on this machine, so anything worth keeping should be turned into a note. Documents are not covered: a PDF is usually a record worth having a copy of.

| Sent from the phone | What happens |
|---|---|
| Photo | Saved, read, answered. Codex gets it as an image, Claude reads it from the path |
| PDF, document, spreadsheet | Saved and read |
| Voice note or audio | Transcribed on this laptop, echoed back, then answered |
| Anything over 20MB | Refused. That is Telegram's own ceiling, not this tool's |

### Voice notes

Speak instead of typing. The recording is transcribed on the laptop, the words are echoed back as "Heard: ...", and the agent answers them. Verified end to end by the vault's owner on 2026-08-07, from a phone, transcript correct.

**It runs entirely on this machine and nothing is uploaded.** A voice note is often dictated somewhere private, and a local model keeps it that way. It also costs nothing per use and works with no internet.

Neither agent reads sound, so this is a separate step in front of them. It needs three things:

```
brew install whisper-cpp ffmpeg
mkdir -p ~/.cache/whisper-cpp
curl -L -o ~/.cache/whisper-cpp/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

`ggml-base.bin` is 141MB and multilingual. Drop `ggml-small.bin` into the same folder for better accuracy on accents and it is preferred automatically.

Missing any of the three is not treated as an error: the voice note is still saved and the reply says transcription is not set up.

**The transcript is always echoed back.** Without that, a misheard word looks like the agent misunderstanding you, and there is no way to tell which happened.

---

## Google permissions, the trap

Claude is given an explicit list of what it may use. **Naming the server, `mcp__personal-google`, is not enough and fails in a way that misleads.** Reads go through under it; every write is refused, and the refusal comes back as:

> user cancelled MCP tool call

Which reads like Google rejecting the request, or an expired token. It is neither. It is this list declining to pass the call on, and no amount of re-authorising will change it. Each tool has to be named in full, `mcp__personal-google__calendar_create_event` and so on.

Deliberately absent, and they should stay absent:

| Not permitted from a phone | Why |
|---|---|
| Sending mail | Drafts only. The vault's server does not expose sending, and this list must not be where that assumption creeps back in |
| Deleting a calendar | Deleting one event is ordinary. Deleting a whole calendar is not |

---

## Which model

**The default on this channel is the fast one**, not the careful one: Haiku for Claude, `gpt-5.6-terra` for Codex. A phone question is usually "what is on Thursday", not a refactor. Measured on the same calendar question, Haiku answered in 18 seconds against 27, and terra in 26 against 36.

This applies only to messages arriving over Telegram. Neither tool's own configuration is touched, so work at the laptop is unaffected.

Change it from the phone:

- `/model` shows the current one
- `/model sonnet` switches, for a question that deserves more thought
- `/model default` goes back to the fast one

**A named model is tried before it is saved.** It is asked to reply "ready", and if it does not, the old one stays and the reason comes back. A typo cannot leave the phone line pointed at a model that does not exist.

Each agent keeps its own model, in `remote_models` in `vault.config.json`. Changing model starts a fresh thread, because a conversation cannot change model halfway.

---

## It remembers the conversation

Ask a follow-up without repeating yourself:

> *What are the open questions on Startup Ideas?*
> *Close the second one.*

The thread stays open for **three hours of quiet**, then the next message starts clean on its own. That cap exists because a thread that never ends drags this morning into tonight, and every message costs more than the last.

`/new` forgets it immediately, which is what to send when you change subject.

**Each agent keeps its own thread.** Claude and Codex cannot read each other's sessions, so `/agent` starts a fresh conversation rather than carrying yours across. Switch back and yours is still there.

If a thread will not reopen, it is dropped and the next message starts a clean one, rather than failing the same way forever.

---

## What it will refuse

| From the phone | Why |
|---|---|
| Deleting anything | Irreversible, and you are not there to catch a mistake |
| `git push --force`, `git reset --hard` | Destroys history that the vault treats as append-only |
| `--no-verify` | Bypasses the check that keeps the vault consistent |
| Installing packages, `sudo`, `curl` | Reaches outside the vault |
| Nothing, on this row | Voice notes work: see Photos and files |

It says so plainly rather than failing silently.

---

## Which agent answers

**From the phone, which is the easy way.** Send `/agent` to see which one is answering, and `/agent codex` or `/agent claude` to change it. `/model` does the same for which model that agent uses. The switch takes effect on the next message and is written to `vault.config.json`, so it survives a restart. An unknown name is refused without taking the bridge down.

Or set it by hand in `vault.config.json`. Leave it out and you get Claude.

```json
{ "remote_agent": "codex" }
```

Both were tested against a real vault on 2026-08-07, same question, same day:

| | Claude | Codex |
|---|---|---|
| Time to answer | about 2 minutes | 44 seconds |
| Reply length | 7 lines | 4 lines |
| Answer | the same | the same |

**They contain the agent differently, and it matters more than the speed.**

Claude restricts **per tool**: an explicit list of what it may use, and nothing outside it. Codex restricts **per directory**: `workspace-write` keeps writes inside the vault, which is real, but there is no way to say "may edit notes, may not run shell". Inside the workspace it can run commands.

So Codex is the weaker containment, and under Codex the refusal list stops being a second layer and becomes load-bearing. Claude is the default for that reason. Choose Codex knowing the trade, not by accident.

Codex needs its own install and sign-in:

```
npm install -g @openai/codex
```

---

## The agent does not know it is on a phone

It runs in the vault exactly as it would at the keyboard, so left alone it reads the vault's writing rules, which assume a laptop screen, and replies with headings and tables. Telegram is sent plain text, so those arrive as literal `##` and `**`.

Every message is therefore prefixed with a short instruction telling the agent where its words are landing: plain text, under eight lines, lead with the answer, one idea. That preamble is `PHONE_PREAMBLE` in the script and it is the only thing making replies phone-shaped. **If answers start arriving as walls of text, that constant is what to look at.**

---

## Known limits

- **A thread belongs to one agent.** Switching with `/agent` starts a separate conversation rather than handing the old one over, because the two vendors cannot read each other's sessions. Each keeps its own, so switching back finds yours where you left it.
- **The laptop must stay awake.** Battery, a forced restart, or a system update all end the session silently on the phone's side. If a reply never comes, that is the first thing to check.
- **The agent can take minutes.** The chat shows "typing..." for the whole time it is working, refreshed every four seconds because Telegram clears it after five. Ten minutes is the ceiling before it gives up. A simple question answers in seconds; anything that reads notes takes a minute or two.
- **Tested end to end 2026-08-07** against a real bot token and a real vault. Two defects were found by that test and are fixed: `--allowedTools` is variadic and swallowed a prompt passed after it, and `--print` reads an inherited stdin as part of the task. The message is now fed on stdin deliberately, which closes both. `--permission-mode acceptEdits` and `--allowedTools` are confirmed against CLI 2.1.223.

---

## Why this exists

Added 2026-08-07, after the vault's owner asked for the full system from a phone: all tools, all mail, everything. Two cloud routes were tried first and both failed the same day, when neither the Claude nor the ChatGPT iPhone app could be granted access to a private vault repository.

The recorded objection this design had to answer is in `discord_remote.py`'s own docstring: *"text from the internet starting a general-purpose agent with write access to somebody's files, unattended. Powerful, and the largest blast radius in this whole system."* That objection stands for a shared channel. The allowlist is the entire argument for why it does not stand here, which is why it fails closed and why the note says not to add a second person to it.

---

## Related

[[System/Skills/Tools/Discord Bridge|Discord Bridge]] | [[System/Skills/Tools/Personal Google|Personal Google]] | [[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Skill Map|Skill Map]]
