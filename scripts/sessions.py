#!/usr/bin/env python3
"""Who is working in this vault right now, and what nobody has saved yet.

A vault is one folder on one disk, and several agents edit it at once. Engineers
avoid this shape entirely by giving everyone their own branch; that trade was
declined here because merging Markdown by hand lands on Camilo, not on the
agents. So the collision has to be reported instead of prevented.

Each session leaves a heartbeat: a small file it rewrites as it works. A session
is over when its pulse stops, which is the only ending that survives a closed
tab, a slept laptop or a crash. Nothing ever writes "closed".

    python3 System/scripts/sessions.py            # the table
    python3 System/scripts/sessions.py --start    # open a heartbeat, then table
    python3 System/scripts/sessions.py --beat     # refresh the pulse, silent
    python3 System/scripts/sessions.py --handover # mark the handover as done

--start and --beat are called by hooks in .claude/settings.json, so a Claude
Code session appears whether or not it read the rules. Anything else (Codex,
the desktop app, Obsidian) must call --start itself or it stays invisible,
which is why absence of a heartbeat is reported as "unknown", never as "clear".
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ACTIVE_MINUTES = 10      # a pulse this fresh means someone is working now
ENDED_HOURS = 6          # no pulse this long means the session is over
UNIDENTIFIED_MINUTES = 10  # a file touched this recently with no owner

EFFORT_RE = re.compile(r"Efforts/([^/]+)/")


def vault_root() -> Path:
    """Find the vault, not the shared system repository inside it.

    `git rev-parse` run from this script answers System/, because the shared
    system is its own repository cloned into the vault. That mistake made the
    table report the system's files as the vault's unsaved work. The marker
    file at the vault root is the only reliable anchor.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".aios-vault").exists():
            return parent
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, cwd=Path.cwd(),
        ).stdout.strip()
        return Path(out)
    except (OSError, subprocess.CalledProcessError):
        return here.parents[2]


VAULT = vault_root()
BEATS = VAULT / "logs" / "sessions"   # logs/ is gitignored, so beats never commit


# --------------------------------------------------------------------------
# writing a heartbeat
# --------------------------------------------------------------------------

def hook_input() -> dict:
    """Claude Code hooks pass JSON on stdin. Never let a parse error surface."""
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return {}


def session_id(data: dict) -> str:
    sid = data.get("session_id") or os.environ.get("AIOS_SESSION_ID")
    if sid:
        return str(sid)[:8]
    # No id available: the process id is unique enough for one machine.
    return "pid%d" % os.getppid()


def edited_effort(data: dict):
    """The effort this tool call is about to write to, or None.

    Read from the hook's own tool input, never from the working tree. Scanning
    recently changed files instead made every beating session claim every
    effort that happened to change while it was alive, so this session claimed
    another agent's Ford Escape files. A claim has to come from what this
    session is doing, not from what merely happened nearby.
    """
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    if not path and data.get("tool_name") == "Bash":
        path = ti.get("command", "")
    m = EFFORT_RE.search(str(path))
    return m.group(1) if m else None


def newest_mtime(path: Path) -> float:
    if path.is_dir():
        times = [os.path.getmtime(os.path.join(r, f))
                 for r, _, fs in os.walk(path) for f in fs]
        return max(times) if times else os.path.getmtime(path)
    return os.path.getmtime(path)


def write_beat(data: dict, starting: bool) -> Path:
    BEATS.mkdir(parents=True, exist_ok=True)
    sid = session_id(data)
    f = BEATS / ("%s.json" % sid)
    now = time.time()

    beat = {}
    if f.exists():
        try:
            beat = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            beat = {}

    if starting or "started" not in beat:
        beat["started"] = now
        beat["handover"] = False
    beat["id"] = sid
    beat["agent"] = os.environ.get("AIOS_AGENT", "Claude Code")
    beat["model"] = data.get("model") or beat.get("model") or "unknown"
    beat["pid"] = os.getppid()
    beat["cwd"] = str(VAULT)
    beat["last_beat"] = now
    # Accumulate, never replace. A session that spent the last half hour on one
    # effort has not stopped owning the one it edited an hour ago, and dropping
    # the older claim is what leaves its files reading as unclaimed.
    claimed = list(beat.get("efforts", []))
    e = edited_effort(data)
    if e and e not in claimed:
        claimed.append(e)
    if claimed:
        beat["efforts"] = claimed[:6]
    f.write_text(json.dumps(beat, indent=2), encoding="utf-8")
    return f


# --------------------------------------------------------------------------
# reading heartbeats
# --------------------------------------------------------------------------

def pid_alive(pid) -> bool | None:
    """True, False, or None when the platform cannot say.

    None matters: on Windows there is no cheap check, so those sessions fall
    back to the six hour rule and are reported as assumed, not as known.
    """
    if not isinstance(pid, int):
        return None
    if os.name == "nt":
        return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None


def load_beats() -> list:
    out = []
    if not BEATS.exists():
        return out
    for f in sorted(BEATS.glob("*.json")):
        try:
            b = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        b["file"] = f
        age_min = (time.time() - b.get("last_beat", 0)) / 60
        alive = pid_alive(b.get("pid"))
        if alive is False or age_min > ENDED_HOURS * 60:
            b["state"] = "ended" if alive is False else "ended?"
        elif age_min <= ACTIVE_MINUTES:
            b["state"] = "ACTIVE"
        else:
            b["state"] = "idle"
        b["age_min"] = age_min
        out.append(b)
    return sorted(out, key=lambda b: -b.get("last_beat", 0))


def commits_by_session(limit: int = 60) -> dict:
    """Map session id to its commits, using the Session: trailer.

    Matching on the SHA or the subject was tried and abandoned: a session that
    merely ran `git log` contains both, so it claimed commits it never made.
    Only a trailer the committing session wrote itself is evidence.
    """
    by = {}
    try:
        log = subprocess.run(
            ["git", "log", "-%d" % limit, "--format=%ad\x1f%s\x1f%b\x1e",
             "--date=format:%Y-%m-%d %H:%M"],
            capture_output=True, text=True, cwd=VAULT,
        ).stdout
    except OSError:
        return by
    for entry in log.split("\x1e"):
        if "\x1f" not in entry:
            continue
        date, subject, body = entry.strip().split("\x1f", 2)
        sid = None
        for line in body.splitlines():
            if line.strip().lower().startswith("session:"):
                sid = line.split(":", 1)[1].strip()[:8]
        if sid:
            by.setdefault(sid, []).append((date, subject))
    return by


def fmt(t) -> str:
    if not t:
        return "-"
    return datetime.fromtimestamp(t).strftime("%m-%d %H:%M")


def print_table(beats: list) -> None:
    commits = commits_by_session()
    hdr = ("Session", "Agent", "Model", "Started", "Last beat", "State",
           "Working on", "Saved", "Last commit", "What")
    rows = [hdr]
    for b in beats:
        mine = commits.get(b.get("id", ""), [])
        last = mine[0] if mine else None
        rows.append((
            b.get("id", "?"),
            b.get("agent", "?")[:12],
            str(b.get("model", "?")).replace("claude-", "")[:8],
            fmt(b.get("started")),
            fmt(b.get("last_beat")),
            b.get("state", "?"),
            ", ".join(b.get("efforts", []))[:26] or "-",
            "Y" if mine else "N",
            last[0][5:] if last else "-",
            (last[1][:30] if last else "-"),
        ))
    if len(rows) == 1:
        print("No heartbeats. Either nothing is running, or an agent that does")
        print("not write one is. This is not proof the vault is free.\n")
        return
    w = [max(len(str(r[i])) for r in rows) for i in range(len(hdr))]
    for i, r in enumerate(rows):
        print("  ".join(str(r[j]).ljust(w[j]) for j in range(len(hdr))).rstrip())
        if i == 0:
            print("  ".join("-" * w[j] for j in range(len(hdr))))
    print()
    print("ACTIVE = pulse under %d min. idle = still open, stepped away."
          % ACTIVE_MINUTES)
    print("ended = process gone. ended? = no pulse for %dh, process not checkable."
          % ENDED_HOURS)


def print_unfinished(beats: list) -> None:
    """Changes sitting in the vault that nobody has saved.

    Attribution is by claim, not by clock: a heartbeat owns a file only if it
    named that effort. Guessing from overlapping time windows was tried and
    produced a confident wrong owner, which is worse than admitting ignorance.
    """
    try:
        out = subprocess.run(["git", "status", "--porcelain"],
                             capture_output=True, text=True, cwd=VAULT).stdout
    except OSError:
        return
    live = [b for b in beats if b.get("state") in ("ACTIVE", "idle")]
    rows, unidentified = [], []
    for line in out.splitlines():
        path = line[3:].strip().strip('"')
        full = VAULT / path
        if not full.exists():
            continue
        try:
            mt = newest_mtime(full)
        except OSError:
            continue
        m = EFFORT_RE.search(path)
        effort = m.group(1) if m else None
        owner = "unclaimed"
        for b in live:
            # A session cannot own a change that predates it. Without this the
            # 2026-08-29 orphans were attributed to a session that opened a day
            # and a half later, purely because it worked in the same effort.
            if mt < b.get("started", 0):
                continue
            if effort and effort in b.get("efforts", []):
                owner = "%s (%s)" % (b.get("id"), b.get("agent"))
                break
        age_h = (time.time() - mt) / 3600
        # Only effort files raise the alarm. System and config files change for
        # a dozen reasons and would drown the signal Camilo actually needs,
        # which is two agents in the same project at the same time.
        if (owner == "unclaimed" and effort
                and age_h * 60 < UNIDENTIFIED_MINUTES):
            unidentified.append(path)
        rows.append((path, mt, owner, age_h))
    if not rows:
        print("\nEverything is committed. Nothing is sitting unsaved.")
        return
    print("\nUNSAVED WORK  (in the vault, not in git)\n")
    w = min(52, max(len(r[0]) for r in rows))
    print("%-*s  %-12s  %s" % (w, "File", "Changed", "Left by"))
    print("%-*s  %-12s  %s" % (w, "-" * w, "-" * 12, "-" * 30))
    for path, mt, owner, age_h in sorted(rows, key=lambda r: -r[1]):
        tail = "  [%.0fh ago]" % age_h if age_h >= 2 else ""
        print("%-*s  %-12s  %s%s" % (w, path[:w], fmt(mt), owner, tail))
    if unidentified:
        print("\nSomeone is working who left no heartbeat. Files changed in the")
        print("last %d minutes that no live session claims:" % UNIDENTIFIED_MINUTES)
        for p in unidentified:
            print("  %s" % p)
        print("Ask before editing these. Do not assume they are abandoned.")
    debts = [b for b in beats
             if b.get("state", "").startswith("ended") and not b.get("handover")]
    if debts:
        print("\nEnded without a handover, so an effort note may be behind:")
        for b in debts:
            print("  %s (%s), last active %s, was in: %s"
                  % (b.get("id"), b.get("agent"), fmt(b.get("last_beat")),
                     ", ".join(b.get("efforts", [])) or "unknown"))


def prune(beats: list, days: int = 14) -> None:
    cutoff = time.time() - days * 86400
    for b in beats:
        if b.get("last_beat", 0) < cutoff:
            try:
                b["file"].unlink()
            except OSError:
                pass


def main() -> int:
    args = sys.argv[1:]

    if "--beat" in args or "--start" in args:
        # A hook must never block the session. Swallow everything.
        try:
            write_beat(hook_input(), starting="--start" in args)
        except Exception:
            return 0
        if "--beat" in args:
            return 0

    if "--handover" in args:
        try:
            data = hook_input()
            f = BEATS / ("%s.json" % session_id(data))
            if f.exists():
                b = json.loads(f.read_text(encoding="utf-8"))
                b["handover"] = True
                f.write_text(json.dumps(b, indent=2), encoding="utf-8")
                print("Handover recorded for session %s." % b.get("id"))
            else:
                print("No heartbeat for this session; nothing to record.")
        except Exception as e:
            print("Could not record the handover: %s" % e)
        return 0

    beats = load_beats()
    prune(beats)
    print("SESSIONS IN THIS VAULT\n")
    print_table([b for b in beats if b["file"].exists()])
    print_unfinished([b for b in beats if b["file"].exists()])
    return 0


if __name__ == "__main__":
    sys.exit(main())
