#!/usr/bin/env python3
"""Talk to this vault from a phone, over Telegram, with the full agent behind it.

This is the design [[discord_remote.py]] deliberately refused to build. Its
docstring is worth repeating, because it was right:

    text from the internet starting a general-purpose agent with write access
    to somebody's files, unattended. Powerful, and the largest blast radius in
    this whole system.

What changed is not the risk, it is one word. `discord_remote` guards a channel
other people can write into, so any message might be from anyone, and the only
safe answer is a fixed menu with no model in the loop. This guards a channel
exactly one person can write into: every message is checked against an
allowlist of Telegram user IDs before anything reads it, and a message from
anyone else is logged and dropped without a reply. It is not text from the
internet. It is the owner, on a phone, and the agent behind it is the same
agent they would get at the laptop.

That single control is what the whole thing rests on, so it is enforced first,
in one place, and it fails closed: an empty allowlist accepts nobody.

Everything else is a second layer rather than the wall:

  * The agent runs with an explicit tool allowlist, not with permission checks
    disabled. It edits notes, reads mail and commits; it does not delete, force
    push, or install anything.
  * Every message in and every reply out is appended to a log, so a session
    that happened while nobody was watching can still be read afterwards.
  * The vault is a git repository and the agent commits, so anything it wrote
    can be undone by the owner at the laptop.

Run it in a visible terminal, never as a background job:

    caffeinate -i python3 System/scripts/telegram_remote.py

Deliberate, and the same reasoning as the Discord remote: this vault once ran
upkeep from a launchd job that died silently for nineteen days because nothing
was watching. A window printing a heartbeat is either there or obviously gone.
`caffeinate -i` stops macOS idle-sleeping, which is what lets the laptop serve
the phone with the lid shut.

First run, to find out your own Telegram user ID:

    python3 System/scripts/telegram_remote.py --pair

It prints the ID of anyone who messages the bot and replies to nobody. Put your
ID in vault.config.json under telegram_allowed_ids, then start it normally.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_paths as _paths

VAULT = _paths.VAULT
API = "https://api.telegram.org"

LOG_FILE = VAULT / "logs" / "telegram_remote.log"
STATE_FILE = VAULT / "logs" / "telegram_state.json"

POLL_TIMEOUT = 25          # Telegram long-poll; the connection is held open.
AGENT_TIMEOUT = 600        # A real task can take minutes. Beyond this, give up.
MAX_MESSAGE_CHARS = 4000   # Telegram's hard limit is 4096; leave room.
MAX_PROMPT_CHARS = 4000
BACKLOG_CAP = 5            # Messages queued while busy; older ones are dropped.
TYPING_REFRESH = 4         # Telegram clears "typing" after about five seconds.

# Which agent answers the phone. Set `remote_agent` in vault.config.json to a
# key of AGENTS below. Claude is the default because its containment is the
# stronger of the two, for the reason recorded on the codex entry.
#
# These flags are the one part of this file that depends on somebody else's
# interface, so each was read off that tool's own help output and then tested,
# rather than assumed.
DEFAULT_AGENT = "claude"

# A phone question is usually "what is on Thursday", not a refactor, so the
# default on this channel is the fast model rather than the careful one. Both
# vaults' own configs stay untouched: this applies only to messages arriving
# over Telegram. Override per agent with `remote_models` in vault.config.json,
# or from the phone with /model.
DEFAULT_MODELS = {"claude": "haiku", "codex": "gpt-5.6-terra"}

# Google, named one tool at a time.
#
# The obvious form is the server prefix, `mcp__personal-google`, and it is a
# trap: reads went through under it and every write was refused with "user
# cancelled MCP tool call", which reads like Google rejecting the request when
# it is this list refusing to pass it on. Nothing was wrong with the account.
# Naming each tool is verbose and it is the only form that actually works.
#
# What is deliberately absent: creating or deleting whole calendars, and
# anything that sends mail. Drafts yes, sending no. The server does not expose
# sending at all, and this list must not become the place that assumes it does.
GOOGLE_TOOLS: List[str] = [
    # This vault's own server, which both agents can reach.
    "mcp__personal-google__calendar_list_calendars",
    "mcp__personal-google__calendar_get_calendar",
    "mcp__personal-google__calendar_list_events",
    "mcp__personal-google__calendar_get_event",
    "mcp__personal-google__calendar_freebusy",
    "mcp__personal-google__calendar_create_event",
    "mcp__personal-google__calendar_update_event",
    "mcp__personal-google__calendar_move_event",
    "mcp__personal-google__calendar_delete_event",
    "mcp__personal-google__gmail_search",
    "mcp__personal-google__gmail_get_message",
    "mcp__personal-google__gmail_list_labels",
    "mcp__personal-google__gmail_create_label",
    "mcp__personal-google__gmail_create_draft",
    "mcp__personal-google__gmail_organize_message",
    "mcp__personal-google__gmail_download_attachment",
    "mcp__personal-google__drive_list",
    "mcp__personal-google__drive_search",
    "mcp__personal-google__drive_info",
    "mcp__personal-google__drive_download",
    "mcp__personal-google__personal_google_status",
    # The host's own connectors, kept as a fallback for a machine where the
    # vault server is not registered.
    "mcp__claude_ai_Google_Calendar__list_calendars",
    "mcp__claude_ai_Google_Calendar__list_events",
    "mcp__claude_ai_Google_Calendar__get_event",
    "mcp__claude_ai_Google_Calendar__search_events",
    "mcp__claude_ai_Google_Calendar__suggest_time",
    "mcp__claude_ai_Google_Calendar__create_event",
    "mcp__claude_ai_Google_Calendar__update_event",
    "mcp__claude_ai_Google_Calendar__delete_event",
    "mcp__claude_ai_Google_Calendar__respond_to_event",
    "mcp__claude_ai_Google_Drive__search_files",
    "mcp__claude_ai_Google_Drive__read_file_content",
    "mcp__claude_ai_Google_Drive__get_file_metadata",
    "mcp__claude_ai_Google_Drive__list_recent_files",
]

# The restriction flags only. How the conversation is started or resumed is
# decided in build_command, so --print lives there rather than here.
# Everything the agent may use, as one comma-separated value. Built rather than
# written out so the Google list stays readable above.
CLAUDE_TOOLS: List[str] = [
    "Read", "Edit", "Write", "Grep", "Glob", "TodoWrite", "WebFetch", "WebSearch",
    "Bash(git status:*)", "Bash(git add:*)", "Bash(git commit:*)",
    "Bash(git push:*)", "Bash(git log:*)", "Bash(git diff:*)", "Bash(git show:*)",
    "Bash(python3 System/scripts/vault_lint.py)",
    "Bash(python3 System/scripts/build_views.py)",
    *GOOGLE_TOOLS,
]

CLAUDE_ARGS: List[str] = [
    "--permission-mode", "acceptEdits",
    "--allowedTools", ",".join(CLAUDE_TOOLS),
]

AGENTS: Dict[str, Dict[str, Any]] = {
    # Claude restricts per tool: the exact list above and nothing else.
    # "client" session: we choose the id and hand it over.
    "claude": {
        "candidates": ["claude", str(Path.home() / ".claude/local/claude")],
        "args": CLAUDE_ARGS,
        "answer": "stdout",
        "session": "client",
        "model_flag": "--model",
    },
    # Codex restricts per directory instead. `workspace-write` keeps writes
    # inside the vault, which is real containment, but there is no way to say
    # "may edit notes, may not run shell": inside the workspace it can run
    # commands. That is weaker than the Claude profile, and it is why the
    # REFUSED list below carries real weight here rather than being a second
    # layer. Recorded rather than hidden, so the choice is made knowingly.
    # "server" session: it invents the id and announces it on its first line
    # of JSON, so it has to be caught rather than chosen.
    "codex": {
        "candidates": ["codex"],
        # Calendar writes ask for approval even though they run outside the
        # shell sandbox. A headless run has nobody to answer, so route those
        # requests to Codex's built-in reviewer. This changes who reviews the
        # call; it does not weaken workspace-write containment.
        "args": ["--sandbox", "workspace-write", "-c",
                 'approvals_reviewer="auto_review"'],
        # `exec resume` accepts no --sandbox at all, so the same restriction has
        # to travel as a config override or a resumed thread silently falls back
        # to whatever the user's own config says. The reviewer override must
        # travel too; resumed conversations are separate CLI invocations.
        "resume_args": ["-c", 'sandbox_mode="workspace-write"', "-c",
                        'approvals_reviewer="auto_review"'],
        "answer": "last-message",  # `codex exec` prints its whole event stream
        "session": "server",
        "model_flag": "-m",
    },
}

# How long a phone conversation stays open. Follow-up questions are the whole
# point, but a thread that never ends drags this morning into tonight and grows
# slower and more expensive with every message. Idle this long and the next
# message starts clean.
SESSION_IDLE_RESET = 3 * 3600

# The agent runs in the vault exactly as it would at the keyboard, so without
# this it has no idea the answer is going to a phone. It reads the vault's
# writing rules, which are written for a laptop screen, and replies with
# headings and tables that arrive as literal ## and ** because Telegram is sent
# plain text. This is the only thing that tells it where its words are landing.
PHONE_PREAMBLE = """You are answering a message the owner sent from their phone,
over Telegram. It will be shown as plain text.

Write for a phone screen:
- No markdown. No #, no **, no tables, no code fences. They arrive as literal characters.
- Answer in under 8 short lines unless explicitly asked for more.
- Lead with the answer. Cut the preamble, the caveats and the closing offer.
- One idea. If there is more, say so in a final line and let them ask.
- Plain sentences and short dashes for lists.

For anything touching Gmail, Calendar or Drive, use this vault's own
personal-google tools. Your platform's built-in Google integration is the
fallback, not the default, and it does not check which account it is using or
enforce this vault's limits. If you end up using it anyway, say so.

The vault's writing rules assume a laptop screen. On this channel, this note
overrides them.

The message:
"""

# Never allowed from a phone, whatever else is configured. These are the actions
# that are either irreversible or reach outside the vault, and the owner is not
# at a keyboard to catch a mistake.
REFUSED = ("rm ", "rm -", "git reset --hard", "git push --force", "--no-verify",
           "sudo ", "npm install", "pip install", "curl ", "chmod ")


class Stop(Exception):
    """The owner asked it to stop."""


class Reload(Exception):
    """The code underneath this process changed."""


SOURCE = Path(__file__).resolve()


def system_version() -> str:
    """Which version of the system this process is actually running.

    Printed at startup and after every reload, and available from the phone as
    /version. It exists because a fix can be written, tested and announced
    against the authoring copy while the machine the owner uses keeps running
    the old one. That happened twice on 2026-08-07. A version on screen makes
    the difference visible instead of leaving it to be inferred from behaviour.
    """
    try:
        r = subprocess.run(["git", "-C", str(SOURCE.parent.parent),
                            "describe", "--tags"],
                           capture_output=True, text=True, timeout=15)
        return r.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def source_stamp() -> float:
    """When this script was last written.

    Updating the system checks out a new version of this very file underneath a
    running process, which then keeps serving the old code until somebody
    remembers to restart it. Watching the file removes the remembering.
    """
    try:
        return SOURCE.stat().st_mtime
    except OSError:
        return 0.0


def reload_self() -> None:
    """Replace this process with the new version of itself.

    execv rather than a wrapper script: it swaps the program inside the same
    process, so whatever is holding the laptop awake around it stays holding it,
    and the terminal window does not change.
    """
    log(f"code changed underneath; reloading into {system_version()}")
    os.execv(sys.executable, [sys.executable, str(SOURCE), *sys.argv[1:]])


def log(message: str, *, to_file: bool = True) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line, flush=True)
    if not to_file:
        return
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass  # A broken log must never take down the bridge.


def token() -> str:
    """The bot token, from the environment or the vault's credentials folder.

    Never printed, not even in an error. A token in a traceback ends up in the
    log file this script writes, which is the one place it must not be.
    """
    env = os.environ.get("VAULT_TELEGRAM_BOT_TOKEN")
    if env:
        return env.strip()
    path = Path(os.environ.get("VAULT_TELEGRAM_TOKEN_FILE") or
                _paths.credential("telegram_bot_token.json.key"))
    if not path.exists():
        sys.exit(f"No Telegram bot token at {path}.\n"
                 "See System/Skills/Tools/Telegram Remote.md for how to make one.")
    try:
        value = (json.loads(path.read_text(encoding="utf-8")).get("token") or "").strip()
    except (OSError, ValueError):
        sys.exit(f"{path} is not readable JSON.")
    if not value or value.startswith("PASTE"):
        sys.exit(f"{path} still holds the placeholder. Paste the real token into it.")
    return value


def allowed_ids() -> List[int]:
    """Who may talk to this vault. Fails closed: no entry means nobody.

    Read fresh rather than cached, so revoking access does not need a restart.
    """
    raw = _paths.vault_config().get("telegram_allowed_ids") or []
    if isinstance(raw, (str, int)):
        raw = [raw]
    out = []
    for item in raw:
        try:
            out.append(int(str(item).strip()))
        except (TypeError, ValueError):
            continue
    return out


def call(method: str, params: Optional[Dict[str, Any]] = None,
         timeout: int = 30) -> Dict[str, Any]:
    url = f"{API}/bot{token()}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        # Strip the URL: it contains the token.
        raise RuntimeError(f"Telegram {method} failed: HTTP {exc.code}") from None
    except OSError as exc:
        # OSError rather than URLError. A plain read timeout is socket.timeout,
        # which is not a URLError, so it escaped and killed the process on the
        # first patch of bad wifi. Everything network-shaped lands here:
        # timeouts, refused connections, DNS, a dropped route. None of them
        # carry the URL, so none of them can leak the token into a log.
        raise RuntimeError(f"Telegram {method} unreachable: "
                           f"{type(exc).__name__}: {exc}") from None
    except ValueError as exc:
        # A truncated or non-JSON body, which happens when a connection dies
        # mid-response. Also not a reason to stop answering the phone.
        raise RuntimeError(f"Telegram {method} returned something unreadable: {exc}") from None


def send(chat_id: int, text: str) -> None:
    """Reply, split across messages if the agent was talkative."""
    text = text.strip() or "(the agent returned nothing)"
    while text:
        chunk, text = text[:MAX_MESSAGE_CHARS], text[MAX_MESSAGE_CHARS:]
        try:
            call("sendMessage", {"chat_id": chat_id, "text": chunk})
        except RuntimeError as exc:
            log(f"could not reply: {exc}")
            return


@contextlib.contextmanager
def typing(chat_id: int):
    """Show "typing..." for as long as the agent is working.

    Telegram clears the indicator after roughly five seconds, so it has to be
    re-sent on a heartbeat rather than set once. This replaced a "Working on
    it." message, which said the same thing but left a line of clutter in the
    chat that was worthless a minute later.

    A failed refresh is swallowed. Losing the indicator is cosmetic and must
    never take down the reply behind it.
    """
    done = threading.Event()

    def beat() -> None:
        while not done.is_set():
            try:
                call("sendChatAction", {"chat_id": chat_id, "action": "typing"})
            except RuntimeError:
                return  # the reply itself will report any real network trouble
            done.wait(TYPING_REFRESH)

    thread = threading.Thread(target=beat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        done.set()
        thread.join(timeout=2)


INBOX = VAULT / "Ideaverse" / "Inbox"
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024  # Telegram's own getFile ceiling.
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}


def download_attachment(file_id: str, suggested: str) -> Optional[Path]:
    """Pull one attachment into the vault's inbox and return where it landed.

    It goes to the inbox rather than a temp folder on purpose: a photo of a
    letter sent from a phone is usually something to deal with later, and a
    file the agent read once and threw away cannot be looked at again.
    """
    try:
        info = (call("getFile", {"file_id": file_id}).get("result") or {})
    except RuntimeError as exc:
        log(f"could not look up an attachment: {exc}")
        return None
    remote = info.get("file_path")
    if not remote:
        return None
    if int(info.get("file_size") or 0) > MAX_DOWNLOAD_BYTES:
        return None

    suffix = Path(remote).suffix or Path(suggested).suffix
    stem = Path(suggested).stem or "attachment"
    safe = "".join(c for c in stem if c.isalnum() or c in " -_")[:60].strip() or "attachment"
    dest = INBOX / f"{datetime.now():%Y-%m-%d %H%M} {safe}{suffix}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    n = 1
    while dest.exists():
        dest = dest.with_name(f"{dest.stem} ({n}){dest.suffix}")
        n += 1

    # The token is in this URL, so nothing about it may reach a log or an error.
    url = f"{API}/file/bot{token()}/{remote}"
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            dest.write_bytes(resp.read())
    except (urllib.error.URLError, OSError):
        log(f"could not download {dest.name}")
        return None
    log(f"saved {dest.relative_to(VAULT)}")
    return dest


AUDIO_SUFFIXES = {".oga", ".ogg", ".opus", ".m4a", ".mp3", ".wav", ".mp4", ".webm"}
WHISPER_MODELS = [
    Path.home() / ".cache/whisper-cpp/ggml-base.bin",
    Path.home() / ".cache/whisper-cpp/ggml-small.bin",
]


def transcribe(audio: Path) -> Optional[str]:
    """Turn a voice note into text, entirely on this machine.

    Runs locally rather than through an API on purpose: a voice note is often
    dictated somewhere private, and this way it never leaves the laptop. Needs
    `whisper-cpp` and `ffmpeg`, and a model file; missing any of them is not an
    error, it means the owner has not set this up and should be told so.

    Telegram sends Opus. whisper.cpp wants 16kHz mono PCM, so ffmpeg converts
    first.
    """
    model = next((m for m in WHISPER_MODELS if m.exists()), None)
    if not model or not shutil.which("whisper-cli") or not shutil.which("ffmpeg"):
        return None
    wav = audio.with_suffix(".16k.wav")
    try:
        conv = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio),
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
            capture_output=True, text=True, timeout=180)
        if conv.returncode != 0 or not wav.exists():
            log("ffmpeg could not convert the audio")
            return None
        # -nt strips timestamps, -np strips the progress banner, so stdout is
        # the words and nothing else.
        r = subprocess.run(
            ["whisper-cli", "-m", str(model), "-f", str(wav), "-nt", "-np"],
            capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"transcription failed: {type(exc).__name__}")
        return None
    finally:
        wav.unlink(missing_ok=True)
    if r.returncode != 0:
        return None
    return " ".join((r.stdout or "").split()).strip() or None


def attachment_of(message: Dict[str, Any]) -> tuple[Optional[str], str]:
    """The file id and a name for whatever is attached, if anything is."""
    if message.get("photo"):
        # Telegram sends the same photo at several sizes; the last is the largest.
        return message["photo"][-1].get("file_id"), "photo.jpg"
    for kind in ("document", "video", "audio", "voice", "video_note"):
        item = message.get(kind)
        if item:
            return item.get("file_id"), item.get("file_name") or f"{kind}"
    return None, ""


def load_offset() -> int:
    try:
        return int(json.loads(STATE_FILE.read_text(encoding="utf-8")).get("offset", 0))
    except (OSError, ValueError, AttributeError):
        return 0


def _update_state(change) -> None:
    """Read, change, write. Every writer must go through this.

    An earlier version had save_offset write `{"offset": n}` wholesale, which
    deleted the open conversation on every incoming message: the thread was
    stored correctly at the end of one message and destroyed at the start of the
    next, so the phone appeared to have no memory at all while the code that
    kept it was working perfectly.
    """
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            state = {}
    except (OSError, ValueError):
        state = {}
    change(state)
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def save_offset(offset: int) -> None:
    _update_state(lambda s: s.__setitem__("offset", offset))


INSTALL_HINT = {
    "claude": "npm install -g @anthropic-ai/claude-code",
    "codex": "npm install -g @openai/codex",
}


def _write_config(update) -> None:
    path = VAULT / "vault.config.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        data = {}
    update(data)
    path.write_text(json.dumps(dict(sorted(data.items())), indent=2) + "\n",
                    encoding="utf-8")


def set_remote_model(agent: str, model: str) -> None:
    """Remember the model per agent, so each keeps its own choice."""
    def apply(data):
        data.setdefault("remote_models", {})[agent] = model
    _write_config(apply)


def set_remote_agent(name: str) -> None:
    """Remember the choice, so a switch from the phone survives a restart."""
    path = VAULT / "vault.config.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        data = {}
    data["remote_agent"] = name
    path.write_text(json.dumps(dict(sorted(data.items())), indent=2) + "\n",
                    encoding="utf-8")


def agent_spec(name: Optional[str] = None) -> Dict[str, Any]:
    """Which agent answers the phone, resolved to a runnable command.

    Raises SystemExit when it cannot be resolved. That is right at startup and
    wrong mid-session, so the /agent command catches it and reports instead of
    letting a typo take the bridge down.
    """
    name = (name or str(_paths.vault_config().get("remote_agent")
                        or DEFAULT_AGENT)).lower()
    if name not in AGENTS:
        sys.exit(f"remote_agent is {name!r} in vault.config.json, but the only "
                 f"choices are: {', '.join(sorted(AGENTS))}.")
    spec = dict(AGENTS[name], name=name)
    configured = _paths.vault_config().get("remote_models") or {}
    spec["model"] = str(configured.get(name) or DEFAULT_MODELS.get(name) or "").strip()
    for candidate in spec["candidates"]:
        try:
            r = subprocess.run([candidate, "--version"], capture_output=True,
                               text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0:
            log(f"agent: {name} on {spec['model'] or 'its default model'}, "
                f"{r.stdout.strip()}")
            spec["binary"] = candidate
            return spec
    sys.exit(f"The {name} CLI is not installed. Install it with:\n"
             f"    {INSTALL_HINT[name]}\n"
             f"then sign in once by running `{name}` before starting this.")


def load_session(agent: str) -> Optional[str]:
    """The open conversation for this agent, if it is still fresh enough."""
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    entry = (state.get("sessions") or {}).get(agent)
    if not entry:
        return None
    if time.time() - float(entry.get("at", 0)) > SESSION_IDLE_RESET:
        return None  # gone stale; the next message starts clean
    return entry.get("id")


def save_session(agent: str, session_id: Optional[str]) -> None:
    def change(state):
        sessions = state.setdefault("sessions", {})
        if session_id:
            sessions[agent] = {"id": session_id, "at": time.time()}
        else:
            sessions.pop(agent, None)
    _update_state(change)


def build_command(spec: Dict[str, Any], resume: Optional[str],
                  reply_file: Optional[Path]) -> tuple[List[str], Optional[str]]:
    """The full command, plus the session id if we are the one choosing it.

    The two agents differ in who owns the identifier. Claude accepts one we
    invent. Codex mints its own and reports it, so for Codex this returns None
    and the id is read out of the output afterwards.
    """
    limits = list(spec["args"])
    model = ([spec["model_flag"], spec["model"]] if spec.get("model") else [])
    if spec["name"] == "claude":
        if resume:
            return ["--print", "--resume", resume, *model, *limits], resume
        fresh = str(uuid.uuid4())
        return ["--print", "--session-id", fresh, *model, *limits], fresh
    # codex. `exec` and `exec resume` do not take the same flags, and resume
    # wants its options before the session id.
    tail = ["--json", *(["--output-last-message", str(reply_file)] if reply_file else [])]
    if resume:
        return ["exec", "resume", *spec["resume_args"], *model, *tail, resume, "-"], None
    return ["exec", *limits, *model, *tail, "-"], None


def thread_id_from(stream: str) -> Optional[str]:
    """Codex announces its thread on the first line of JSONL output."""
    for line in stream.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        found = event.get("thread_id") or event.get("session_id")
        if found:
            return str(found)
    return None


def ask_agent(spec: Dict[str, Any], prompt: str,
              image: Optional[Path] = None) -> str:
    """Hand one message to the agent, in the vault, and return what it said."""
    lowered = prompt.lower()
    for bad in REFUSED:
        if bad in lowered:
            return (f"Not from the phone. That asks for `{bad.strip()}`, which is "
                    "either irreversible or reaches outside the vault, and you are "
                    "not at a keyboard to catch a mistake. Ask me at the laptop.")

    binary = spec["binary"]
    # Some agents print their whole event stream to stdout, so the final answer
    # has to be collected from a file instead of scraped out of the transcript.
    last_message: Optional[Path] = None
    if spec["answer"] == "last-message":
        last_message = Path(tempfile.mkstemp(prefix="aios-reply-", suffix=".txt")[1])

    resume = load_session(spec["name"])
    args, session_id = build_command(spec, resume, last_message)
    if image is not None and spec["name"] == "codex":
        args += ["-i", str(image)]  # Claude reads it from the path in the prompt.
    # Only the first message of a thread carries the channel instructions. On a
    # resumed one they are already in the conversation, and repeating them every
    # turn crowds out the thing actually being asked.
    payload = prompt if resume else PHONE_PREAMBLE + prompt

    try:
        # The message goes in on stdin, not as a trailing argument. Two reasons,
        # both found by smoke-testing this rather than reading the help text.
        # `--allowedTools` is variadic, so a prompt placed after it is swallowed
        # as another tool name and the agent exits saying it got no input. And
        # `--print` reads stdin when it is open, so an inherited stream becomes
        # part of the task: the first test had the agent answer a question about
        # the calling terminal's heredoc instead of the message. Feeding stdin
        # deliberately closes both holes.
        r = subprocess.run([binary, *args], cwd=str(VAULT), input=payload,
                           capture_output=True, text=True, timeout=AGENT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return (f"Gave up after {AGENT_TIMEOUT // 60} minutes. The task may still "
                "have half-finished, so check `git status` at the laptop.")
    except OSError as exc:
        return f"Could not start the agent: {exc}"
    finally:
        if last_message and last_message.exists():
            answer = last_message.read_text(encoding="utf-8", errors="replace").strip()
            last_message.unlink(missing_ok=True)
        else:
            answer = ""

    out = answer or (r.stdout or "").strip()
    if r.returncode != 0 and not out:
        # A resume that fails leaves the thread poisoned, so drop it: the next
        # message starts a clean one rather than failing again forever.
        if resume:
            save_session(spec["name"], None)
            log(f"{spec['name']} could not resume {resume}; thread dropped")
            return ("That thread would not reopen, so I have started a fresh one. "
                    "Ask again and it will work, without the earlier context.")
        return f"The agent exited with an error.\n{(r.stderr or '').strip()[:1000]}"

    # Codex mints its own id and announces it, so it is read back here.
    save_session(spec["name"], session_id or thread_id_from(r.stdout or "") or resume)
    return out


def handle(spec: Optional[Dict[str, Any]], message: Dict[str, Any],
           pairing: bool) -> None:
    chat_id = (message.get("chat") or {}).get("id")
    user = message.get("from") or {}
    user_id = user.get("id")
    name = user.get("username") or user.get("first_name") or "unknown"
    text = (message.get("text") or "").strip()

    if pairing:
        log(f"PAIRING: message from {name}, id {user_id}. "
            f"Put this in vault.config.json under telegram_allowed_ids.")
        return

    permitted = allowed_ids()
    if not permitted:
        log("allowlist is empty, so nobody is allowed. Run with --pair first.")
        return
    if user_id not in permitted:
        # No reply. An unknown sender learns nothing, not even that this exists.
        log(f"REFUSED message from {name}, id {user_id}: {text[:80]!r}")
        return

    file_id, suggested = attachment_of(message)
    attachment: Optional[Path] = None
    if file_id:
        text = (message.get("caption") or "").strip()
        with typing(chat_id):
            attachment = download_attachment(file_id, suggested)
        if not attachment:
            send(chat_id, "That would not download. Anything over 20MB has to "
                          "go on the laptop.")
            return
        if attachment.suffix.lower() in AUDIO_SUFFIXES:
            with typing(chat_id):
                spoken = transcribe(attachment)
            if not spoken:
                send(chat_id, f"Saved to Inbox as {attachment.name}, but I could "
                              "not turn it into words. Either transcription is "
                              "not set up on the laptop, or the recording was "
                              "silent. See Telegram Remote.md.")
                return
            log(f"transcribed: {spoken[:150]}")
            # Echoed back because a wrong transcription otherwise looks like the
            # agent misunderstanding, and the owner cannot tell which happened.
            send(chat_id, f"Heard: {spoken}")
            text = f"{spoken}\n\n{text}".strip() if text else spoken
            attachment = None  # a voice note is a message, not a file to read
        else:
            text = (f"An attachment just arrived and is saved at "
                    f"{attachment.relative_to(VAULT)}\nRead it, then: "
                    f"{text or 'tell me what it is and what I should do with it.'}")

    if not text:
        send(chat_id, "Empty message. Send text, a photo, or a file.")
        return
    if attachment is None and text in ("/version", "/v"):
        send(chat_id, f"System {system_version()}, {spec['name']} on "
                      f"{spec.get('model') or 'its default model'}.\n\n"
                      "If a fix was announced and this is not the version it "
                      "shipped in, the laptop has not picked it up.")
        return
    if attachment is None and text in ("/restart", "/reload"):
        send(chat_id, "Reloading.")
        raise Reload
    if attachment is None and text in ("/stop", "/quit"):
        send(chat_id, "Stopping. The terminal on the laptop is now closed.")
        raise Stop
    if attachment is None and text in ("/new", "/reset", "/clear"):
        if load_session(spec["name"]):
            save_session(spec["name"], None)
            send(chat_id, "Fresh start. I have forgotten the thread we were on.")
        else:
            send(chat_id, "Already starting fresh.")
        return
    if attachment is None and text.split()[0] == "/model":
        choice = text.partition(" ")[2].strip()
        if not choice:
            send(chat_id, f"{spec['name']} is on {spec['model'] or 'its own default'}.\n\n"
                          f"Change it with /model <name>, for example "
                          f"/model {DEFAULT_MODELS.get(spec['name'], 'sonnet')}\n"
                          "/model default goes back to the fast one.")
            return
        wanted = "" if choice.lower() in ("default", "reset") else choice
        previous = spec.get("model", "")
        spec["model"] = wanted or DEFAULT_MODELS.get(spec["name"], "")
        probe = ask_agent(spec, "Reply with exactly: ready")
        if "ready" not in probe.lower()[:200]:
            spec["model"] = previous
            send(chat_id, f"{choice} did not answer, so I have stayed on "
                          f"{previous or 'the default'}.\n\n{probe[:300]}")
            return
        set_remote_model(spec["name"], spec["model"])
        # A thread belongs to the model that started it.
        save_session(spec["name"], None)
        log(f"model for {spec['name']} set to {spec['model']} from the phone")
        send(chat_id, f"{spec['name']} is now on {spec['model']}. "
                      "Starting a fresh thread, since a conversation cannot "
                      "change model halfway.")
        return
    if attachment is None and text.split()[0] == "/agent":
        choice = text.partition(" ")[2].strip().lower()
        if not choice:
            send(chat_id, f"Answering as {spec['name']}.\n\n"
                          f"Switch with: /agent "
                          f"{' or /agent '.join(sorted(AGENTS))}")
            return
        if choice not in AGENTS:
            send(chat_id, f"I only know {', '.join(sorted(AGENTS))}.")
            return
        if choice == spec["name"]:
            send(chat_id, f"Already {choice}.")
            return
        try:
            fresh = agent_spec(choice)
        except SystemExit as exc:
            send(chat_id, f"Cannot switch to {choice}.\n\n{exc}")
            return
        set_remote_agent(choice)
        # Mutated rather than rebound: the polling loop holds this same dict.
        spec.clear()
        spec.update(fresh)
        log(f"agent switched to {choice} from the phone")
        carried = "picking up where you left off" if load_session(choice) else "starting fresh"
        send(chat_id, f"Now answering as {choice} on "
                      f"{fresh.get('model') or 'its default model'}, {carried}. "
                      "A thread belongs to one agent and cannot move between them. "
                      "This survives a restart.")
        return
    if attachment is None and text in ("/start", "/help"):
        send(chat_id, "This is your vault, with the same agent you get at the "
                      "laptop. Ask it anything you would ask there.\n\n"
                      "It can read and write your notes, search the web, read "
                      "your mail and calendar, and commit its work.\n\n"
                      "Send a photo or a file and it lands in your Inbox and "
                      "gets read. Add a caption to say what you want done with "
                      "it. Voice notes are saved but not understood: nothing "
                      "here transcribes audio yet.\n\n"
                      "It cannot delete files, force push, install anything or "
                      "spend money from here. Those need you at the laptop.\n\n"
                      "It remembers the conversation, so you can ask a "
                      "follow-up without repeating yourself. After three hours "
                      "quiet it starts fresh on its own.\n\n"
                      f"Answering as {spec['name']} on "
                      f"{spec.get('model') or 'its default model'}.\n"
                      "/agent changes who answers, /model changes which one.\n"
                      "/new forgets the thread and starts clean.\n"
                      "/version says which build is answering.\n"
                      "/restart reloads after an update, though it does that "
                      "by itself.\n"
                      "/stop ends the session on the laptop.")
        return
    if attachment is None and len(text) > MAX_PROMPT_CHARS:
        send(chat_id, f"That is {len(text)} characters and I cap at "
                      f"{MAX_PROMPT_CHARS}. Send it in pieces.")
        return

    log(f"IN  from {name}: {text[:200]}")
    with typing(chat_id):
        image = attachment if (attachment and
                               attachment.suffix.lower() in IMAGE_SUFFIXES) else None
        reply = ask_agent(spec, text, image=image)
    if not reply.strip():
        # An empty agent result used to become an empty Telegram bubble. Silence
        # is clearer and lets the next owner message continue the thread normally.
        log(f"OUT to {name}: no reply")
        return
    log(f"OUT to {name}: {reply[:200]}")
    send(chat_id, reply)


def main() -> int:
    ap = argparse.ArgumentParser(description="Talk to this vault from Telegram.")
    ap.add_argument("--pair", action="store_true",
                    help="Print the ID of anyone who messages, and reply to nobody.")
    ap.add_argument("--once", action="store_true",
                    help="Handle whatever is waiting, then exit. For testing.")
    args = ap.parse_args()

    token()  # Fail now, loudly, rather than on the first message.
    spec = None if args.pair else agent_spec()

    if args.pair:
        log("PAIRING MODE. Message your bot from the phone you want to use.")
        log("Nothing is executed and nobody gets a reply. Ctrl-C when done.")
    else:
        permitted = allowed_ids()
        if not permitted:
            sys.exit("No telegram_allowed_ids in vault.config.json, so nobody is "
                     "allowed to talk to this vault. Run --pair first to find "
                     "your ID. This fails closed on purpose.")
        log(f"vault: {VAULT}")
        log(f"system: {system_version()}  ({SOURCE})")
        log(f"listening. {len(permitted)} allowed sender(s). Ctrl-C to stop.")

    started_with = source_stamp()
    offset = load_offset()
    while True:
        try:
            resp = call("getUpdates",
                        {"offset": offset, "timeout": POLL_TIMEOUT,
                         "allowed_updates": json.dumps(["message"])},
                        timeout=POLL_TIMEOUT + 10)
        except RuntimeError as exc:
            log(f"{exc}. Retrying in 30s.")
            time.sleep(30)
            continue
        except Exception as exc:
            # Last line of defence. This process is meant to sit there for days,
            # so no single unexpected fault may end it: the failure the owner
            # sees is a phone that stopped answering with nobody watching. The
            # terminal still shows what happened, and the loop carries on.
            log(f"unexpected {type(exc).__name__}: {exc}. Retrying in 30s.")
            time.sleep(30)
            continue

        updates = resp.get("result") or []
        if len(updates) > BACKLOG_CAP:
            log(f"{len(updates)} messages queued; handling the last {BACKLOG_CAP}.")
            for skipped in updates[:-BACKLOG_CAP]:
                offset = max(offset, skipped.get("update_id", 0) + 1)
            updates = updates[-BACKLOG_CAP:]

        for update in updates:
            offset = max(offset, update.get("update_id", 0) + 1)
            save_offset(offset)
            message = update.get("message")
            if not message:
                continue
            try:
                handle(spec, message, args.pair)
            except Stop:
                log("stopped by request.")
                return 0
            except Reload:
                reload_self()
            except Exception as exc:  # one bad message must not end the session
                log(f"error handling a message: {type(exc).__name__}: {exc}")

        if not args.pair and source_stamp() != started_with:
            reload_self()

        if args.once:
            log("--once: nothing left waiting.")
            return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nstopped.")
        sys.exit(0)
