#!/usr/bin/env python3
"""Do agents read the entry files, and which skills do they actually use?

Two questions, one scanner, because both are answered by reading the local
Claude Code and Codex transcripts and neither can be answered by asking an
agent to report on itself.

    python3 System/scripts/entry_compliance.py           entry-file compliance
    python3 System/scripts/entry_compliance.py --skills  per-skill usage
    python3 System/scripts/entry_compliance.py --json

CLAUDE.md and AGENTS.md both say to read Me.md and Active Context before any
task. Whether that happens has never been checked. The default mode counts it.
It exists because the answer turned out to be "usually not, in short sessions",
and a rule nobody follows is worse than no rule: it looks like protection while
providing none. Re-run it after changing the entry path to see whether the
change moved the number.

--skills answers the separate question of which skills earn their place in the
startup listing. The listing is capped, so every exposed skill spends budget in
every session whether or not it fires. A skill nobody reaches is paying rent.

Both modes read what the runtime writes, never what an agent chose to record:
Claude logs a Skill tool call carrying the skill id, and a Read carrying the
note path; Codex logs the shell call whose arguments hold the path. An agent
that decides not to mention using a skill still leaves both traces.

Counts only. No transcript text is ever printed or returned: these files are
known to contain credentials that past sessions read, and they sit outside the
vault where .gitignore cannot reach them.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from collections import defaultdict

CLAUDE_DIR = pathlib.Path("~/.claude/projects").expanduser()
CODEX_DIR = pathlib.Path("~/.codex/sessions").expanduser()

# This script lives in the system repo, so the system half is never a guess.
SYSTEM = pathlib.Path(__file__).resolve().parent.parent
VAULT_MARKER = ".aios-vault"


def _find_vault_root() -> pathlib.Path:
    """The folder holding this installation's own notes. Mirrors build_views."""
    override = os.environ.get("VAULT_ROOT")
    if override:
        return pathlib.Path(override).expanduser().resolve()
    for candidate in pathlib.Path(__file__).resolve().parents:
        if (candidate / VAULT_MARKER).exists():
            return candidate
    return SYSTEM


VAULT = _find_vault_root()
# A vault has two skill trees and both are exposed the same way: System/Skills
# ships with the shared system, Skills/ at the vault root holds this person's
# private ones. Scanning only the first hides BigQuery and the Delivery Hero
# workflows, which is how the first run of this reported 38 skills for a
# catalogue of 49.
SKILL_ROOTS = list(dict.fromkeys([SYSTEM / "Skills", VAULT / "Skills"]))

ENTRY_FILES = ("Me.md", "Active Context")
# Below this, a transcript is an aborted run, a one-shot or a background job
# rather than a working session, and counting it drowns the signal.
REAL_SESSION_TURNS = 2
BUCKETS = [("short", 0, 200_000), ("medium", 200_000, 1_000_000), ("long", 1_000_000, 1 << 60)]

# One session touching the same skill note this many times is not using the
# skill, it is looping on it: the session that wrote it, or one debugging it.
# Telegram Remote showed 284 reads across 12 sessions, 272 of them in the six
# sessions that built the skill on 2026-08-07. Without this the usage table
# reports authoring effort as popularity.
LOOP_TOUCHES = 8
# Codex runs edits through the shell, so the write shows up as an argument.
CODEX_WRITE_MARKERS = ("apply_patch", "cat >", "tee ", "sed -i", " > ")
CLAUDE_WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# One command naming several skill notes at once is an inventory sweep, a build
# or a grep across the tree, not a session using those skills. Counting it once
# per name is how every skill in the vault looked like it had been used once.
ENUMERATION_AT = 3
EXPOSED_VALUES = {"true", "yes", "all", "claude_code"}


# --------------------------------------------------------------- skill catalog

def _frontmatter(path: pathlib.Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "-", "#")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip("\"'")
    return fm


def catalog() -> dict[str, tuple[str, bool]]:
    """{note stem: (skill id, exposed)} for every skill note that has an id."""
    out: dict[str, tuple[str, bool]] = {}
    for root in SKILL_ROOTS:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.md")):
            fm = _frontmatter(p)
            sid = fm.get("id")
            if sid:
                out[p.stem] = (sid, fm.get("expose", "").lower() in EXPOSED_VALUES)
    return out


def _note_regex(stems) -> re.Pattern | None:
    if not stems:
        return None
    alt = "|".join(re.escape(s) for s in sorted(stems, key=len, reverse=True))
    # Either tree: "System/Skills/Tools/X.md" or the vault's own "Skills/Tools/X.md".
    return re.compile(r"Skills/[^\"']*?/(" + alt + r")\.md")


# ------------------------------------------------------------ entry compliance

def _hits(blob: str) -> tuple[bool, bool]:
    return ("Me.md" in blob), ("Active Context" in blob)


def scan_claude(path: pathlib.Path) -> tuple[int, bool, bool]:
    """(real user turns, read Me, read Active Context)"""

    turns, me, ac = 0, False, False
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            msg = rec.get("message") or {}
            content = msg.get("content")
            if msg.get("role") == "user":
                if isinstance(content, str) and content.strip():
                    turns += 1
                elif isinstance(content, list) and any(
                    isinstance(b, dict) and b.get("type") == "text" for b in content
                ):
                    turns += 1
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        h_me, h_ac = _hits(json.dumps(b.get("input", {})))
                        me, ac = me or h_me, ac or h_ac
    return turns, me, ac


def scan_codex(path: pathlib.Path) -> tuple[int, bool, bool]:

    turns, me, ac = 0, False, False
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            p = rec.get("payload")
            if not isinstance(p, dict):
                continue
            ptype = p.get("type")
            if ptype == "user_message" or (ptype == "message" and p.get("role") == "user"):
                turns += 1
            if ptype in ("custom_tool_call", "function_call", "local_shell_call"):
                h_me, h_ac = _hits(json.dumps(p))
                me, ac = me or h_me, ac or h_ac
    return turns, me, ac


def collect() -> list[dict]:
    rows = []
    for base, scanner, agent in (
        (CLAUDE_DIR, scan_claude, "claude"),
        (CODEX_DIR, scan_codex, "codex"),
    ):
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.jsonl")):
            try:
                turns, me, ac = scanner(f)
            except OSError:
                continue
            rows.append(
                {
                    "agent": agent,
                    "bytes": f.stat().st_size,
                    "turns": turns,
                    "read_both": me and ac,
                    "read_ac": ac,
                    "read_any": me or ac,
                }
            )
    return rows


def bucket_of(n: int) -> str:
    for name, lo, hi in BUCKETS:
        if lo <= n < hi:
            return name
    return "long"


# ---------------------------------------------------------------- skill usage

def skills_claude(path, stems, rx) -> dict[str, dict]:
    """{skill id or stem: {'touches': n, 'wrote': bool}} for one transcript."""

    seen: dict[str, dict] = defaultdict(lambda: {"touches": 0, "wrote": False})
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            content = (rec.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                name, inp = b.get("name"), b.get("input") or {}
                if name == "Skill" and inp.get("skill"):
                    key = str(inp["skill"])
                    seen[key]["touches"] += 1
                    continue
                if not rx:
                    continue
                found = {m.group(1) for m in rx.finditer(json.dumps(inp))}
                if len(found) >= ENUMERATION_AT:
                    continue
                for stem in found:
                    key = stems[stem][0]
                    seen[key]["touches"] += 1
                    if name in CLAUDE_WRITE_TOOLS:
                        seen[key]["wrote"] = True
    return seen


def skills_codex(path, stems, rx) -> dict[str, dict]:
    seen: dict[str, dict] = defaultdict(lambda: {"touches": 0, "wrote": False})
    if not rx:
        return seen
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            p = rec.get("payload")
            if not isinstance(p, dict):
                continue
            if p.get("type") not in ("custom_tool_call", "function_call", "local_shell_call"):
                continue
            blob = json.dumps(p)
            found = {m.group(1) for m in rx.finditer(blob)}
            if len(found) >= ENUMERATION_AT:
                continue
            wrote = any(mk in blob for mk in CODEX_WRITE_MARKERS)
            for stem in found:
                key = stems[stem][0]
                seen[key]["touches"] += 1
                if wrote:
                    seen[key]["wrote"] = True
    return seen


def usage() -> tuple[dict, dict, int]:
    """(per-skill counts, catalog, real sessions scanned)"""

    stems = catalog()
    rx = _note_regex(stems.keys())
    ids = {sid for sid, _ in stems.values()}
    counts: dict[str, dict] = defaultdict(
        lambda: {"claude": 0, "codex": 0, "authoring": 0, "unknown": False}
    )
    sessions = 0
    for base, entry_scan, skill_scan, agent in (
        (CLAUDE_DIR, scan_claude, skills_claude, "claude"),
        (CODEX_DIR, scan_codex, skills_codex, "codex"),
    ):
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.jsonl")):
            try:
                turns, _, _ = entry_scan(f)
                if turns < REAL_SESSION_TURNS:
                    continue
                sessions += 1
                for key, d in skill_scan(f, stems, rx).items():
                    if d["wrote"] or d["touches"] >= LOOP_TOUCHES:
                        counts[key]["authoring"] += 1
                    else:
                        counts[key][agent] += 1
                    if key not in ids:
                        counts[key]["unknown"] = True
            except OSError:
                continue
    return counts, stems, sessions


def print_usage() -> int:
    counts, stems, sessions = usage()
    by_id = {sid: exposed for sid, exposed in stems.values()}
    if not stems:
        print("no skill notes found", file=sys.stderr)
        return 1

    print("SKILL USAGE: which skills do sessions actually reach?")
    print("=" * 72)
    print(f"real sessions scanned ({REAL_SESSION_TURNS}+ user turns): {sessions}")
    print(f"skills in catalogue: {len(by_id)}   exposed: {sum(by_id.values())}")
    print()
    print(f"{'skill':<28}{'auto':>6}{'claude':>8}{'codex':>7}{'used':>6}{'built':>7}")
    print("-" * 72)

    rows = []
    for sid, exposed in sorted(by_id.items()):
        c = counts.get(sid, {})
        used = c.get("claude", 0) + c.get("codex", 0)
        rows.append((used, sid, exposed, c.get("claude", 0), c.get("codex", 0),
                     c.get("authoring", 0)))
    for used, sid, exposed, cl, cx, auth in sorted(rows, key=lambda r: (-r[0], r[1])):
        print(f"{sid:<28}{'yes' if exposed else '-':>6}{cl:>8}{cx:>7}{used:>6}{auth:>7}")

    extra = sorted(k for k, v in counts.items() if v.get("unknown"))
    if extra:
        print()
        print("reached but not in this vault's catalogue (bundled or plugin skills):")
        print("  " + ", ".join(extra))

    dead = sorted(sid for used, sid, exposed, *_ in rows if exposed and used == 0)
    if dead:
        print()
        print("EXPOSED BUT NEVER REACHED IN A REAL SESSION:")
        for sid in dead:
            print(f"  {sid}")
        print()
        print("These spend startup budget in every session. Before unexposing one,")
        print("ask whether the agent could know to look it up: a rule that fires")
        print("when the agent does not know it needs it cannot be routed by hand.")
    print()
    print("'built' counts sessions that wrote the note or touched it "
          f"{LOOP_TOUCHES}+ times.")
    print("Those are authoring sessions and are excluded from 'used'.")
    return 0


# ---------------------------------------------------------------------- main

def main() -> int:
    if "--skills" in sys.argv:
        return print_usage()

    rows = collect()
    if not rows:
        print("no transcripts found", file=sys.stderr)
        return 1
    real = [r for r in rows if r["turns"] >= REAL_SESSION_TURNS]

    if "--json" in sys.argv:
        print(json.dumps({"transcripts": len(rows), "real_sessions": len(real),
                          "read_both": sum(r["read_both"] for r in real),
                          "read_active_context": sum(r["read_ac"] for r in real)}, indent=2))
        return 0

    print("ENTRY COMPLIANCE: did the session read Me.md and Active Context?")
    print("=" * 64)
    print(f"transcripts on this machine : {len(rows)}")
    print(f"real sessions ({REAL_SESSION_TURNS}+ user turns): {len(real)}")
    if not real:
        return 0
    both = sum(r["read_both"] for r in real)
    ac = sum(r["read_ac"] for r in real)
    # Since the card, the rules arrive in CLAUDE.md and AGENTS.md whether the
    # session cooperates or not, so reading Me.md is no longer required and
    # "read both" understates compliance. Active Context is the file that still
    # depends on the agent choosing to open it, and is the number to watch.
    print(f"read Active Context         : {ac}  ({100*ac/len(real):.0f}%)   <- the one that matters")
    print(f"read both (pre-card metric) : {both}  ({100*both/len(real):.0f}%)")
    print()
    print(f"{'agent':<8}{'length':<9}{'sessions':>9}{'read AC':>9}{'rate':>7}")
    print("-" * 64)
    for agent in ("claude", "codex"):
        for name, _, _ in BUCKETS:
            b = [r for r in real if r["agent"] == agent and bucket_of(r["bytes"]) == name]
            if not b:
                continue
            y = sum(r["read_ac"] for r in b)
            print(f"{agent:<8}{name:<9}{len(b):>9}{y:>9}{100*y/len(b):>6.0f}%")
    print()
    print("A low rate in short sessions is the finding to watch: it means what")
    print("Camilo is currently working on is skipped exactly where a quick")
    print("unconsidered action is most likely.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
