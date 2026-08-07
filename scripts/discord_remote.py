#!/usr/bin/env python3
"""Remote control for this vault over Discord. A fixed menu, not an agent.

Why it is built this way. The obvious design is to poll a channel and hand each
message to `claude -p`, so anything you can ask in person you can ask from a
phone. That means text from the internet starting a general-purpose agent with
write access to somebody's files, unattended. Powerful, and the largest blast
radius in this whole system.

So this does the boring thing instead. A message must match one of a few known
commands. There is no language model in the loop, so there is nothing to talk
around: a message that is not on the menu gets a polite list of the menu. The
worst an attacker with the channel can do is read some notes and append text to
an inbox file.

Exactly one command writes anything, `note`, and it only ever appends and then
commits, so git can undo it. Nothing here deletes, sends, or spends.

Run it in a visible terminal, never as a background job:

    caffeinate -i python3 scripts/discord_remote.py

Deliberate. This vault once ran upkeep from a launchd job that died silently for
nineteen days because nothing was watching. A window printing a heartbeat is
either there or obviously gone. `caffeinate -i` stops macOS idle-sleeping.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_paths as _paths

VAULT_ROOT = _paths.VAULT
BRIDGE = VAULT_ROOT / "scripts" / "discord_bridge.py"
STATE_FILE = VAULT_ROOT / "scripts" / "logs" / "remote_state.json"
EFFORTS_DIR = VAULT_ROOT / "Ideaverse" / "Efforts"
INBOX_DIR = VAULT_ROOT / "Ideaverse" / "Inbox"
API = "https://discord.com/api/v10"

DEFAULT_INTERVAL = 20
MIN_INTERVAL = 10
BACKLOG_CAP = 10
MAX_REPLY_CHARS = 1800
MAX_NOTE_CHARS = 1000
MAX_SEARCH_HITS = 8
SNIPPET_CHARS = 120


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def _vault_config() -> dict:
    path = VAULT_ROOT / "vault.config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _token() -> str:
    env = os.environ.get("VAULT_DISCORD_BOT_TOKEN")
    if env:
        return env.strip()
    path = Path(os.environ.get("VAULT_DISCORD_TOKEN_FILE") or
                _paths.credential("discord_bot_token.json.key"))
    if not path.exists():
        sys.exit("No Discord bot token found. See Skills/Tools/Discord Bridge.md")
    try:
        return (json.loads(path.read_text(encoding="utf-8")).get("token") or "").strip()
    except (OSError, ValueError):
        sys.exit("The token file is not readable JSON.")


def _frontmatter(path: Path) -> Dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: Dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _active_efforts() -> List[Dict[str, str]]:
    if not EFFORTS_DIR.exists():
        return []
    found = []
    for d in sorted(EFFORTS_DIR.iterdir()):
        main = d / f"{d.name}.md"
        if not (d.is_dir() and main.exists()):
            continue
        fm = _frontmatter(main)
        if fm.get("status") == "active":
            found.append({"name": d.name, "next": fm.get("next", "")})
    return found


# --------------------------------------------------------------------------
# The menu. Every command is either read-only or append-then-commit.
# --------------------------------------------------------------------------

def cmd_help(_arg: str) -> str:
    return (
        "Commands I understand while you are away:\n"
        "  status        how the vault is doing\n"
        "  next          next action for each active project\n"
        "  note <text>   save a thought to the inbox\n"
        "  search <text> find notes mentioning something\n"
        "  help          this list\n\n"
        "Anything else needs you at the laptop. I cannot send messages, delete "
        "anything, or spend money from here, by design."
    )


def cmd_status(_arg: str) -> str:
    lines = []
    try:
        proc = subprocess.run(
            [sys.executable, str(VAULT_ROOT / "scripts" / "vault_lint.py")],
            cwd=str(VAULT_ROOT), capture_output=True, text=True, timeout=120,
        )
        lines.append("Vault is clean." if proc.returncode == 0 else "Lint found problems; needs a look on the laptop.")
    except (OSError, subprocess.TimeoutExpired):
        lines.append("Could not run lint.")

    efforts = _active_efforts()
    lines.append(f"{len(efforts)} active project(s).")

    try:
        proc = subprocess.run(
            ["git", "log", "--since=7 days ago", "--oneline"],
            cwd=str(VAULT_ROOT), capture_output=True, text=True, timeout=30,
        )
        lines.append(f"{len([l for l in proc.stdout.splitlines() if l.strip()])} change(s) in the last 7 days.")
    except (OSError, subprocess.TimeoutExpired):
        pass

    try:
        proc = subprocess.run(["git", "status", "--porcelain"], cwd=str(VAULT_ROOT),
                              capture_output=True, text=True, timeout=30)
        dirty = len([l for l in proc.stdout.splitlines() if l.strip()])
        if dirty:
            lines.append(f"{dirty} uncommitted change(s) waiting.")
    except (OSError, subprocess.TimeoutExpired):
        pass

    return "\n".join(lines)


def cmd_next(_arg: str) -> str:
    efforts = _active_efforts()
    if not efforts:
        return "No active projects yet."
    out = []
    for e in efforts:
        nxt = e["next"] or "(no next action set)"
        out.append(f"- {e['name']}: {nxt}")
    return "Next actions:\n" + "\n".join(out)


def cmd_note(arg: str) -> str:
    """The only command that writes. Appends, then commits, so git can undo it."""
    text = arg.strip()
    if not text:
        return "Nothing to save. Use: note <what you want to remember>"
    if len(text) > MAX_NOTE_CHARS:
        return f"That is {len(text)} characters; I cap notes at {MAX_NOTE_CHARS} from a phone."

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    target = INBOX_DIR / f"{date.today().isoformat()} - Captured from phone.md"
    stamp = datetime.now().strftime("%H:%M")
    if not target.exists():
        target.write_text(
            f"# Captured from phone, {date.today().isoformat()}\n\n"
            "Sent from Discord while away from the laptop. Process these into the "
            "right place when convenient.\n\n", encoding="utf-8")
    with target.open("a", encoding="utf-8") as fh:
        fh.write(f"- **{stamp}** {text}\n")

    committed = "saved"
    try:
        subprocess.run(["git", "add", str(target.relative_to(VAULT_ROOT))],
                       cwd=str(VAULT_ROOT), capture_output=True, timeout=30, check=False)
        proc = subprocess.run(["git", "commit", "-q", "-m", "Capture from phone"],
                              cwd=str(VAULT_ROOT), capture_output=True, text=True, timeout=60)
        if proc.returncode == 0:
            committed = "saved and committed"
    except (OSError, subprocess.TimeoutExpired):
        committed = "saved but not committed; commit it on the laptop"

    return f"{committed} to today's inbox note."


def cmd_search(arg: str) -> str:
    query = arg.strip()
    if len(query) < 3:
        return "Give me at least three characters to search for."
    pattern = re.compile(re.escape(query), re.I)
    hits: List[str] = []
    for path in sorted(VAULT_ROOT.rglob("*.md")):
        rel = path.relative_to(VAULT_ROOT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 40)
            snippet = " ".join(text[start:m.start() + SNIPPET_CHARS].split())
            hits.append(f"- {rel}\n  ...{snippet}...")
            if len(hits) >= MAX_SEARCH_HITS:
                break
    if not hits:
        return f"Nothing mentions \"{query}\"."
    return f"Found {len(hits)}:\n" + "\n".join(hits)


COMMANDS = {
    "help": cmd_help,
    "status": cmd_status,
    "next": cmd_next,
    "note": cmd_note,
    "search": cmd_search,
}


def dispatch(content: str) -> str:
    """Match the first word against the menu. No fuzzy matching, no guessing."""
    stripped = (content or "").strip()
    if not stripped:
        return cmd_help("")
    verb, _, rest = stripped.partition(" ")
    handler = COMMANDS.get(verb.lower())
    if handler is None:
        return (
            f"I do not know \"{verb[:30]}\". While you are away I only handle a "
            "fixed set of commands, on purpose.\n\n" + cmd_help("")
        )
    return handler(rest)


# --------------------------------------------------------------------------
# Polling loop
# --------------------------------------------------------------------------

def fetch_new(channel: str, after: Optional[str]) -> List[Dict[str, Any]]:
    query = {"limit": "50"}
    if after:
        query["after"] = after
    req = urllib.request.Request(f"{API}/channels/{channel}/messages?{urllib.parse.urlencode(query)}")
    req.add_header("Authorization", f"Bot {_token()}")
    req.add_header("User-Agent", "VaultRemote (personal use)")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return list(reversed(json.loads(resp.read().decode("utf-8"))))


def post(text: str, channel: str) -> None:
    text = text[:MAX_REPLY_CHARS].strip() or "(no reply)"
    try:
        subprocess.run([sys.executable, str(BRIDGE), "post", text, "--channel", channel],
                       capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        log(f"could not post reply: {error}")


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Discord remote control for this vault. Fixed commands only.")
    parser.add_argument("--channel", default=None)
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    parser.add_argument("--once", action="store_true", help="Handle whatever is waiting, then exit. Useful for testing.")
    parser.add_argument("--dry-run", action="store_true", help="Print replies instead of posting them.")
    args = parser.parse_args()

    cfg = _vault_config()
    channel = (args.channel or cfg.get("discord_private_channel_id") or "").strip()
    if not channel.isdigit():
        sys.exit("No channel configured. Set discord_private_channel_id in vault.config.json, or pass --channel.")

    interval = max(MIN_INTERVAL, args.interval)
    state = _load_state()
    last_seen = state.get(channel)

    if not last_seen:
        try:
            recent = fetch_new(channel, None)
        except Exception as error:  # noqa: BLE001
            sys.exit(f"Could not reach Discord: {error}")
        last_seen = recent[-1]["id"] if recent else None
        state[channel] = last_seen
        _save_state(state)
        log("first run: starting from now, ignoring earlier messages")

    log(f"listening on {channel} every {interval}s. Commands: status, next, note, search, help. Ctrl-C to stop.")
    if args.dry_run:
        log("DRY RUN: replies printed, not posted")

    while True:
        try:
            messages = fetch_new(channel, last_seen)
            human = [m for m in messages if not (m.get("author") or {}).get("bot")]
            if messages:
                last_seen = messages[-1]["id"]
                state[channel] = last_seen
                _save_state(state)

            if len(human) > BACKLOG_CAP:
                dropped = len(human) - BACKLOG_CAP
                human = human[-BACKLOG_CAP:]
                log(f"backlog: handling last {BACKLOG_CAP}, skipping {dropped}")

            for m in human:
                content = m.get("content") or ""
                log(f"{(m.get('author') or {}).get('username')}: {content[:60]}")
                reply = dispatch(content)
                if args.dry_run:
                    print("--- would reply ---\n" + reply + "\n-------------------", flush=True)
                else:
                    post(reply, channel)

            if not human:
                log("nothing new")

            if args.once:
                return 0

        except urllib.error.HTTPError as error:
            wait = 60 if error.code == 429 else interval
            log(f"Discord returned {error.code}; retrying in {wait}s")
            time.sleep(wait)
            continue
        except urllib.error.URLError as error:
            log(f"network unreachable ({error.reason}); will retry")
        except KeyboardInterrupt:
            log("stopped")
            return 0
        except Exception as error:  # noqa: BLE001 - one bad cycle must not kill the loop
            log(f"unexpected error, continuing: {error}")

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            log("stopped")
            return 0


if __name__ == "__main__":
    sys.exit(main())
