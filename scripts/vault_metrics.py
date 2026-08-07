#!/usr/bin/env python3
"""
Vault health and throughput metrics for the AI OS.

Prints a markdown snapshot (for the weekly review note) and appends one CSV row
per run to scripts/logs/metrics.csv so trends are measurable over time.

Usage:
    python3 scripts/vault_metrics.py            # markdown to stdout + CSV append
    python3 scripts/vault_metrics.py --no-csv   # stdout only
"""

import csv
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_views import VAULT, parse_frontmatter, collect_efforts, STALE_DAYS


def git(*args):
    return subprocess.run(["git", *args], cwd=VAULT, capture_output=True, text=True).stdout.strip()


def md_files():
    return [f for f in VAULT.rglob("*.md")
            if not any(s in f.parts for s in (".git", ".claude", ".obsidian", "node_modules"))]


def usage_stats(days=7):
    """Token usage from local Claude Code transcripts (~/.claude/projects).
    Dedupes by message id; a message can appear on multiple jsonl lines."""
    import json
    from datetime import timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stats = {"sessions": 0, "in": 0, "cache_read": 0, "cache_create": 0, "out": 0, "skills": 0}
    seen_msgs = set()
    for proj in Path.home().glob(".claude/projects/*Obsidian-Vault-AI-OS*"):
        for f in proj.glob("*.jsonl"):
            if datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc) < cutoff:
                continue
            session_counted = False
            try:
                for line in f.open(encoding="utf-8"):
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = e.get("timestamp", "")
                    if ts and datetime.fromisoformat(ts.replace("Z", "+00:00")) < cutoff:
                        continue
                    msg = e.get("message") or {}
                    u = msg.get("usage")
                    if u and msg.get("id") not in seen_msgs:
                        seen_msgs.add(msg.get("id"))
                        stats["in"] += u.get("input_tokens", 0)
                        stats["cache_read"] += u.get("cache_read_input_tokens", 0)
                        stats["cache_create"] += u.get("cache_creation_input_tokens", 0)
                        stats["out"] += u.get("output_tokens", 0)
                        session_counted = True
                    for blk in (msg.get("content") or []):
                        if isinstance(blk, dict) and blk.get("type") == "tool_use" and blk.get("name") == "Skill":
                            stats["skills"] += 1
            except OSError:
                continue
            if session_counted:
                stats["sessions"] += 1
    total_in = stats["in"] + stats["cache_read"] + stats["cache_create"]
    stats["cache_pct"] = round(100 * stats["cache_read"] / total_in) if total_in else 0
    stats["total"] = total_in + stats["out"]
    return stats



def lint_findings():
    """Warning counts from vault_lint, so vault health becomes a trend, not a snapshot.

    Errors are not counted: the pre-commit hook makes them un-committable, so they
    are always zero here. Warnings are the interesting signal, because nothing
    forces them to be fixed and they accumulate quietly.
    """
    counts = {"lint_warnings": 0, "expired_content": 0, "boundary_violations": 0}
    try:
        out = subprocess.run(
            [sys.executable, str(VAULT / "scripts/vault_lint.py")],
            capture_output=True, text=True, timeout=180,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return counts
    seen = False
    for line in out.splitlines():
        if line.startswith("[!] Warnings"):
            seen = True
            continue
        if not seen or not line.startswith("  "):
            continue
        counts["lint_warnings"] += 1
        if "next action references" in line or "is " in line and "d old;" in line:
            counts["expired_content"] += 1
        elif "names specific effort" in line:
            counts["boundary_violations"] += 1
    return counts


def main():
    today = date.today()
    files = md_files()

    # Freshness
    efforts = [e for e in collect_efforts() if e.get("status") == "active"]
    stale = []
    for e in efforts:
        try:
            age = (today - date.fromisoformat(e.get("updated", ""))).days
        except ValueError:
            age = None
        if age is not None and age > STALE_DAYS:
            stale.append((e["_name"], age))
    fresh_pct = round(100 * (len(efforts) - len(stale)) / len(efforts)) if efforts else 100

    # Open decisions (Active Context table)
    ac = (VAULT / "Maps & Manuals/Active Context.md").read_text(encoding="utf-8")
    decisions = [r.split("|")[1].strip() for r in ac.splitlines()
                 if r.startswith("|") and "Pending" in r]

    # Throughput (last 7 days)
    commits_7d = len([l for l in git("log", "--since=7.days", "--oneline").splitlines() if l])
    created = git("log", "--since=7.days", "--diff-filter=A", "--name-only", "--format=")
    notes_created_7d = len({l for l in created.splitlines() if l.endswith(".md")})

    # Capture hygiene
    inbox = [f for f in (VAULT / "Ideaverse/Inbox").iterdir()
             if f.name not in ("README.md",) and not f.name.startswith(".")]
    raw_sources = [f.stem for f in (VAULT / "Ideaverse/Sources").glob("*.md")
                   if parse_frontmatter(f).get("status") == "raw"]

    # Knowledge and graph
    atlas = [f for f in (VAULT / "Ideaverse/Atlas").rglob("*.md") if f.name != "Atlas Index.md"]
    link_re = re.compile(r'\[\[([^|\]\\\[]+)(?:\\?\|[^\]]+)?\]\]')
    edges = sum(len(link_re.findall(re.sub(r'```.*?```', '', f.read_text(encoding="utf-8"), flags=re.S)))
                for f in files)

    # Automation heartbeat: weekly review streak (consecutive ISO weeks ending now)
    weeks = {f.stem.split(" ")[0] for f in (VAULT / "Ideaverse/Calendar").glob("*Weekly Review.md")}

    def prev_week(y, w):
        return (y, w - 1) if w > 1 else (y - 1, date(y - 1, 12, 28).isocalendar()[1])

    streak = 0
    y, w, _ = today.isocalendar()
    if f"{y}-W{w:02d}" not in weeks:  # this week's Friday run may not have fired yet
        y, w = prev_week(y, w)
    while f"{y}-W{w:02d}" in weeks:
        streak += 1
        y, w = prev_week(y, w)

    rows = [
        ("Active efforts fresh (updated <= 30d)", f"{fresh_pct}% ({len(efforts) - len(stale)}/{len(efforts)})"),
        ("Stale efforts", ", ".join(f"{n} ({a}d)" for n, a in stale) or "none"),
        ("Open decisions pending", f"{len(decisions)}: {', '.join(decisions) or 'none'}"),
        ("Commits last 7d", commits_7d),
        ("Notes created last 7d", notes_created_7d),
        ("Inbox items unprocessed", len(inbox)),
        ("Sources still raw", len(raw_sources)),
        ("Atlas notes (permanent knowledge)", len(atlas)),
        ("Graph edges / notes", f"{edges} / {len(files)} ({edges / len(files):.1f} per note)"),
        ("Weekly review streak", f"{streak} week(s)"),
    ]

    u = usage_stats()
    rows += [
        ("Sessions last 7d (with token activity)", u["sessions"]),
        ("Tokens last 7d (total processed)", f"{u['total']:,}"),
        ("Context reuse (cache hit rate)", f"{u['cache_pct']}%"),
        ("Fresh input tokens last 7d (non-cached)", f"{u['in'] + u['cache_create']:,}"),
        ("Output tokens last 7d", f"{u['out']:,}"),
        ("Tokens per commit", f"{u['total'] // commits_7d:,}" if commits_7d else "n/a"),
        ("Skill invocations last 7d", u["skills"]),
    ]

    print("### System metrics (generated)\n")
    print("| Metric | Value |")
    print("|---|---|")
    for k, v in rows:
        print(f"| {k} | {v} |")

    lf = lint_findings()
    if "--no-csv" not in sys.argv:
        csv_path = VAULT / "logs/metrics.csv"
        csv_path.parent.mkdir(exist_ok=True)
        new = not csv_path.exists()
        with csv_path.open("a", newline="") as fh:
            w_ = csv.writer(fh)
            if new:
                w_.writerow(["date", "active_efforts", "stale_efforts", "open_decisions",
                             "commits_7d", "notes_created_7d", "inbox", "raw_sources",
                             "atlas_notes", "notes", "edges", "weekly_streak",
                             "sessions_7d", "tokens_7d", "cache_pct", "out_tokens_7d", "skill_calls_7d",
                             "lint_warnings", "expired_content", "boundary_violations"])
            w_.writerow([today.isoformat(), len(efforts), len(stale), len(decisions),
                         commits_7d, notes_created_7d, len(inbox), len(raw_sources),
                         len(atlas), len(files), edges, streak,
                         u["sessions"], u["total"], u["cache_pct"], u["out"], u["skills"],
                         lf["lint_warnings"], lf["expired_content"], lf["boundary_violations"]])


if __name__ == "__main__":
    main()
