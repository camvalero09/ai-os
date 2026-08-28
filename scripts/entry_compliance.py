#!/usr/bin/env python3
"""Do agents actually read the entry files before working?

CLAUDE.md and AGENTS.md both say to read Me.md and Active Context before any
task. Whether that happens has never been checked. This counts it, across both
Claude Code and Codex transcripts on this machine.

It exists because the answer turned out to be "usually not, in short sessions",
and a rule nobody follows is worse than no rule: it looks like protection while
providing none. Re-run it after changing the entry path to see whether the
change moved the number.

    python3 System/scripts/entry_compliance.py
    python3 System/scripts/entry_compliance.py --json

Counts only. No transcript text is ever printed or returned: these files are
known to contain credentials that past sessions read, and they sit outside the
vault where .gitignore cannot reach them.
"""

from __future__ import annotations

import json
import pathlib
import sys

CLAUDE_DIR = pathlib.Path("~/.claude/projects").expanduser()
CODEX_DIR = pathlib.Path("~/.codex/sessions").expanduser()

ENTRY_FILES = ("Me.md", "Active Context")
# Below this, a transcript is an aborted run, a one-shot or a background job
# rather than a working session, and counting it drowns the signal.
REAL_SESSION_TURNS = 2
BUCKETS = [("short", 0, 200_000), ("medium", 200_000, 1_000_000), ("long", 1_000_000, 1 << 60)]


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
                    "read_any": me or ac,
                }
            )
    return rows


def bucket_of(n: int) -> str:
    for name, lo, hi in BUCKETS:
        if lo <= n < hi:
            return name
    return "long"


def main() -> int:
    rows = collect()
    if not rows:
        print("no transcripts found", file=sys.stderr)
        return 1
    real = [r for r in rows if r["turns"] >= REAL_SESSION_TURNS]

    if "--json" in sys.argv:
        print(json.dumps({"transcripts": len(rows), "real_sessions": len(real),
                          "read_both": sum(r["read_both"] for r in real)}, indent=2))
        return 0

    print("ENTRY COMPLIANCE: did the session read Me.md and Active Context?")
    print("=" * 64)
    print(f"transcripts on this machine : {len(rows)}")
    print(f"real sessions ({REAL_SESSION_TURNS}+ user turns): {len(real)}")
    if not real:
        return 0
    both = sum(r["read_both"] for r in real)
    print(f"read both                   : {both}  ({100*both/len(real):.0f}%)")
    print()
    print(f"{'agent':<8}{'length':<9}{'sessions':>9}{'read both':>11}{'rate':>7}")
    print("-" * 64)
    for agent in ("claude", "codex"):
        for name, _, _ in BUCKETS:
            b = [r for r in real if r["agent"] == agent and bucket_of(r["bytes"]) == name]
            if not b:
                continue
            y = sum(r["read_both"] for r in b)
            print(f"{agent:<8}{name:<9}{len(b):>9}{y:>11}{100*y/len(b):>6.0f}%")
    print()
    print("A low rate in short sessions is the finding to watch: it means the")
    print("rules are being skipped exactly where a quick unconsidered action is")
    print("most likely, which is what they exist to prevent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
