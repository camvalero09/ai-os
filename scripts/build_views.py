#!/usr/bin/env python3
"""
Generates the derived views of the AI OS vault from note frontmatter.

Frontmatter is the single source of truth (status, updated, summary, next).
This script rewrites the content between marker pairs:

    <!-- BEGIN GENERATED: view-name -->
    ...replaced on every run, never edit by hand...
    <!-- END GENERATED: view-name -->

Hand-written content outside markers is never touched.

Usage:
    python3 scripts/build_views.py           # regenerate views in place
    python3 scripts/build_views.py --check   # exit 1 if any view is out of date
"""

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

# The system repository root. This script lives in it, so this is never a guess.
# Standalone that is the repo itself; installed it is <vault>/System.
SYSTEM = Path(__file__).resolve().parent.parent

VAULT_MARKER = ".aios-vault"


def _find_vault_root() -> Path:
    """The folder holding this installation's own notes.

    The system is shared and the content is not, so the two can sit in different
    places and the scripts must not assume they are the same folder. Resolution
    order: an explicit VAULT_ROOT wins; otherwise walk up from this script
    looking for the marker file that every content vault carries; otherwise
    assume the system repo is being run standalone and is its own vault.
    """
    override = os.environ.get("VAULT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    for candidate in Path(__file__).resolve().parents:
        if (candidate / VAULT_MARKER).exists():
            return candidate
    return SYSTEM


VAULT = _find_vault_root()
STALE_DAYS = 30
ARCHIVE_DAYS = 60


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"')
    return fm


def wikilink(rel_path_no_ext: str, display: str) -> str:
    return f"[[{rel_path_no_ext}|{display}]]"


def wikilink_table(rel_path_no_ext: str, display: str) -> str:
    """Wikilink for use inside markdown tables: the pipe must be escaped
    or Obsidian treats it as a column separator and drops the graph edge."""
    return f"[[{rel_path_no_ext}\\|{display}]]"


def parse_date(value: str):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def days_since(value: str):
    d = parse_date(value)
    return (date.today() - d).days if d else None


# ---------- data collection ----------

def collect_efforts():
    efforts = []
    for d in sorted((VAULT / "Ideaverse/Efforts").iterdir()):
        if not d.is_dir():
            continue
        main = d / f"{d.name}.md"
        if not main.exists():
            continue
        fm = parse_frontmatter(main)
        fm["_name"] = d.name
        fm["_dir"] = d.name
        fm["_link"] = wikilink_table(f"Ideaverse/Efforts/{d.name}/{d.name}", d.name)
        efforts.append(fm)
    return efforts


def collect_atlas():
    notes = []
    for p in sorted((VAULT / "Ideaverse/Atlas").rglob("*.md")):
        if p.name == "Atlas Index.md":
            continue
        fm = parse_frontmatter(p)
        rel = p.relative_to(VAULT).with_suffix("")
        fm["_link"] = wikilink_table(str(rel), p.stem)
        notes.append(fm)
    return notes


def collect_sources():
    sources = []
    for p in sorted((VAULT / "Ideaverse/Sources").glob("*.md")):
        if p.name == "Sources Index.md":
            continue
        fm = parse_frontmatter(p)
        rel = p.relative_to(VAULT).with_suffix("")
        fm["_link"] = wikilink_table(str(rel), p.stem)
        sources.append(fm)
    return sources


def collect_outputs():
    """Every finished piece of work, wherever it lives.

    Outputs sit inside the project that produced them, so that a project folder
    holds its own artifacts rather than pointing at a shared pile. A flat folder
    had no relationship to the work it came from: three verdicts written on one
    day sat unlinked and the next session did not know they existed.

    The top-level folder still exists for work belonging to no project, and both
    are collected here so this index stays the single place to answer "what has
    been produced".
    """
    outputs = []
    roots = [(VAULT / "Ideaverse/Outputs", None)]
    efforts_dir = VAULT / "Ideaverse/Efforts"
    if efforts_dir.is_dir():
        for d in sorted(efforts_dir.iterdir()):
            if (d / "Outputs").is_dir():
                roots.append((d / "Outputs", d.name))

    for base, effort in roots:
      for p in sorted(base.rglob("*")):
        if p.is_dir() or p.name == "Outputs Index.md" or p.name.startswith("."):
            continue
        parts = p.relative_to(base).parts
        sub = parts[0] if len(parts) > 1 else ""
        entry = {"_name": p.name,
                 "_project": effort or (sub or ""),
                 "_group": sub if effort else "",
                 "_effort": effort or ""}
        m = re.match(r"^(\d{4}-\d{2}(?:-\d{2})?)", p.name)
        entry["_date"] = m.group(1) if m else ""
        if p.suffix == ".md":
            fm = parse_frontmatter(p)
            rel = p.relative_to(VAULT).with_suffix("")
            entry["_cell"] = wikilink_table(str(rel), p.stem)
            entry["_purpose"] = fm.get("summary", "")
        else:
            entry["_cell"] = f"`{p.name}`"
            entry["_purpose"] = ""
        outputs.append(entry)
    return outputs


# ---------- view renderers ----------

def render_efforts_tables() -> str:
    efforts = collect_efforts()
    active, stalled, closed = [], [], []
    for e in efforts:
        status = e.get("status", "unknown")
        if status in ("closed", "archived"):
            closed.append(e)
        elif status == "active":
            age = days_since(e.get("updated"))
            (stalled if age is not None and age > STALE_DAYS else active).append(e)
        else:
            active.append(e)

    lines = ["## Active", ""]
    lines += ["| Effort | Next action | Blocked on | Open questions | Last updated |",
              "|---|---|---|---|---|"]
    for e in active:
        d = VAULT / "Ideaverse/Efforts" / e["_dir"] if e.get("_dir") else None
        q = open_question_count(d) if d else 0
        lines.append(f"| {e['_link']} | {e.get('next', '')} | {e.get('blocked_on', '') or '-'} "
                     f"| {q or '-'} | {e.get('updated', '')} |")
    lines += ["", f"## Stalled (no movement in {STALE_DAYS}+ days)", ""]
    if stalled:
        lines += ["| Effort | Goal (one line) | Next action | Last updated |", "|---|---|---|---|"]
        for e in stalled:
            lines.append(f"| {e['_link']} | {e.get('summary', '')} | {e.get('next', '')} | {e.get('updated', '')} |")
        lines += ["", f"Stalled efforts move to `Ideaverse/Archive/` after {ARCHIVE_DAYS} days without movement."]
    else:
        lines.append("*None.*")
    lines += ["", "## Closed or archived", ""]
    if closed:
        lines += ["| Effort | Outcome | Status | Last updated |", "|---|---|---|---|"]
        for e in closed:
            lines.append(f"| {e['_link']} | {e.get('summary', '')} | {e.get('status', '')} | {e.get('updated', '')} |")
    else:
        lines.append("*None yet.*")
    return "\n".join(lines)



OPEN_ROW = re.compile(r"^\|([^|]+)\|([^|]*)\|([^|]*)\|(.*)\|\s*$")


def open_question_count(effort_dir) -> int:
    """How many questions this project is still carrying.

    Read from the Open questions table in the project note rather than a
    frontmatter field, so the number cannot disagree with the table it counts.
    A question is open until its row says otherwise.
    """
    note = effort_dir / f"{effort_dir.name}.md"
    if not note.exists():
        return 0
    body = note.read_text(encoding="utf-8")
    if "## Open questions" not in body:
        return 0
    section = body.split("## Open questions", 1)[1].split("\n---", 1)[0]
    n = 0
    for line in section.splitlines():
        m = OPEN_ROW.match(line.strip())
        if not m or m.group(1).strip().lower().startswith(("question", "---")):
            continue
        if "open" in m.group(3).lower() and "closed" not in m.group(3).lower():
            n += 1
    return n


NEXT_ACTION_CHARS = 150


def _first_action(text: str) -> str:
    """The first sentence of a next action, capped.

    The full field is in the effort note and the table links to it, so
    repeating all of it here made Active Context carry 620 words that already
    existed one hop away. One sentence answers the question this table is for,
    which is "what is the next thing on each project", not "brief me".
    """
    text = (text or "").strip()
    if not text:
        return ""
    first = re.split(r"(?<=[.:])\s", text, maxsplit=1)[0].strip()
    if len(first) > NEXT_ACTION_CHARS:
        first = first[:NEXT_ACTION_CHARS].rsplit(" ", 1)[0] + "..."
    return first + (" [...]" if len(first) < len(text) else "")


def render_active_context_efforts() -> str:
    efforts = collect_efforts()
    # One line per project, which is the view actually wanted when asking
    # "where is everything". Not one line per open question: ten questions from
    # one project, opened at different stages and unrelated to each other, is
    # noise rather than a status.
    lines = ["| Project | Status | Next action | Blocked on | Open questions |",
             "|---|---|---|---|---|"]
    for e in efforts:
        # A section called "Active efforts" that lists finished ones is a lie
        # the reader has to check every time. Closed work is in the Efforts
        # Index, which is what that index is for.
        if e.get("status") in ("archived", "closed"):
            continue
        status = e.get("status", "unknown")
        age = days_since(e.get("updated"))
        if status == "active" and age is not None and age > STALE_DAYS:
            status = f"active (stale {age}d)"
        d = VAULT / "Ideaverse/Efforts" / e["_dir"] if e.get("_dir") else None
        q = open_question_count(d) if d else 0
        lines.append(f"| {e['_link']} | {status} | {_first_action(e.get('next', ''))} "
                     f"| {e.get('blocked_on', '') or '-'} | {q or '-'} |")
    return "\n".join(lines)


def render_atlas_notes() -> str:
    lines = ["| Note | Domain | Summary | Updated |", "|---|---|---|---|"]
    for n in collect_atlas():
        lines.append(f"| {n['_link']} | {n.get('domain', '')} | {n.get('summary', '')} | {n.get('updated', '')} |")
    return "\n".join(lines)


def render_sources_table() -> str:
    lines = ["| File | Status | Summary | Processed into |", "|---|---|---|---|"]
    for s in collect_sources():
        processed = " · ".join(
            wikilink_table(p.strip(), p.strip().split("/")[-1])
            for p in s.get("processed_into", "").split(";") if p.strip()
        )
        lines.append(f"| {s['_link']} | {s.get('status', '')} | {s.get('summary', '')} | {processed} |")
    return "\n".join(lines)


def render_outputs_table() -> str:
    outputs = collect_outputs()
    if not outputs:
        return "*No outputs yet.*"
    groups = {}
    for o in outputs:
        groups.setdefault(o["_project"], []).append(o)
    # projects first (alphabetical), work belonging to none last
    order = sorted(groups, key=lambda k: (k == "", k.lower()))
    blocks = []
    for project in order:
        label = project if project else "Belongs to no project"
        rows = ["| File | Date | What it is |", "|---|---|---|"]
        for o in sorted(groups[project], key=lambda x: x["_date"], reverse=True):
            rows.append(f"| {o['_cell']} | {o['_date']} | {o['_purpose']} |")
        blocks.append(f"### {label}\n\n" + "\n".join(rows))
    return "\n\n".join(blocks)


def collect_skills(subdir):
    """Every skill note the agent can reach, from both layers.

    A vault has two skill trees. `System/Skills/` comes from the shared system
    repository and is identical in every installation. `Skills/` at the vault
    root holds skills belonging to this person alone and is never shared. Both
    are usable; only the first travels.
    """
    skills = []
    for layer, base in (("system", SYSTEM / subdir), ("personal", VAULT / subdir)):
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            fm = parse_frontmatter(p)
            rel = p.relative_to(VAULT).with_suffix("")
            fm["_link"] = wikilink_table(str(rel), p.stem)
            fm["_rel_md"] = str(p.relative_to(VAULT))
            fm["_title"] = p.stem
            fm["_layer"] = layer
            skills.append(fm)
    return skills


def _skill_rows(skills):
    lines = ["| Skill | Use when | Auto-loads |", "|---|---|---|"]
    for s in skills:
        auto = "yes" if is_exposed(s) else ""
        lines.append(f"| {s['_link']} | {s.get('summary', '')} | {auto} |")
    return lines


def _render_skill_map(subdir: str) -> str:
    skills = collect_skills(subdir)
    system = [s for s in skills if s["_layer"] == "system"]
    personal = [s for s in skills if s["_layer"] == "personal"]
    lines = _skill_rows(system)
    if personal:
        lines += ["", "### Your own, not part of the shared system", ""]
        lines += _skill_rows(personal)
    return "\n".join(lines)


def render_skill_map_workflows() -> str:
    return _render_skill_map("Skills/Workflows")


def render_skill_map_tools() -> str:
    return _render_skill_map("Skills/Tools")


LOADER_MARK = "generated by scripts/build_views.py"
# The provenance line is visible text, not an HTML comment: agent security
# scanners treat hidden comments in an instruction file as smuggled prompt
# content and drop the whole file. Any rewording must still contain
# LOADER_MARK verbatim, because that substring is how generate_loaders
# recognises the files it owns and may delete.


# Where each agent looks for skills. Adding an agent is a new row here and
# nothing else: a source note declares whether a skill is exposed, never to
# whom. Keeping vendor names out of the notes is what lets the model change
# while the system stays.
SKILL_TARGETS = (
    ".claude/skills",   # Claude Code
    ".agents/skills",   # Codex; scanned from the working directory to the repo root
)


def is_exposed(fm) -> bool:
    """Whether a skill note should be rendered as a loader for every agent.

    `expose: true` is the agent-neutral spelling. `expose: claude_code` was the
    original and is still honoured, so notes written before this change, and
    adopters who have not updated theirs, keep working.
    """
    return str(fm.get("expose", "")).strip().lower() in {
        "true", "yes", "all", "claude_code",
    }


def render_loader(fm) -> str:
    name = fm.get("id", "")
    desc = fm.get("summary", "").rstrip(".")
    triggers = fm.get("triggers", "")
    description = f"{desc}. Use when: {triggers}."
    description = '"' + description.replace('"', '\\"') + '"'
    return f"""---
name: {name}
description: {description}
---

# {fm['_title']} (loader)

> This file is {LOADER_MARK} from "{fm['_rel_md']}". Edit that note, not this file.

**Read and apply `{fm['_rel_md']}`** (relative to the vault root). Do not proceed with the task until you have read it. That note is the canonical version; this loader only routes to it.

This skill stacks with Me.md and Active Context; on conflict, Me.md wins.
"""


def generate_loaders(check: bool):
    """Write <target>/<id>/SKILL.md for every exposed skill, in every target.

    One canonical note per skill under Skills/, one generated pointer per agent.
    The pointers are disposable: delete a target directory, regenerate, and it
    is back, which is the test that keeps this an adapter rather than a second
    home for the content.
    """
    changed = []
    exposed = [s for s in collect_skills("Skills/Workflows") + collect_skills("Skills/Tools")
               if is_exposed(s) and s.get("id")]
    wanted = {s["id"] for s in exposed}
    for rel_dir in SKILL_TARGETS:
        skills_dir = VAULT / rel_dir
        for s in exposed:
            target = skills_dir / s["id"] / "SKILL.md"
            content = render_loader(s)
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                changed.append(str(target.relative_to(VAULT)))
                if not check:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
        if skills_dir.exists():
            for d in sorted(skills_dir.iterdir()):
                skill_md = d / "SKILL.md"
                if d.is_dir() and d.name not in wanted and skill_md.exists() \
                        and LOADER_MARK in skill_md.read_text(encoding="utf-8"):
                    changed.append(f"{d.relative_to(VAULT)} (remove: no longer exposed)")
                    if not check:
                        skill_md.unlink()
                        d.rmdir()
    return changed


ENTRY_FILES = ("CLAUDE.md", "AGENTS.md")
WIKILINK_RE = re.compile(r"\[\[([^\]|\\]+)(?:\\?\|[^\]]*)?\]\]")
CARD_RE = re.compile(r"<!-- BEGIN CARD -->\n(.*?)<!-- END CARD -->", re.DOTALL)


def read_card(path: Path) -> str:
    """The text between the card markers, or "" if the file has no card."""
    if not path.exists():
        return ""
    m = CARD_RE.search(path.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""


def generate_entry_files(check: bool):
    """Write CLAUDE.md and AGENTS.md from two cards, personal then shared.

    Agents load their entry file automatically; they read Me.md only if they
    decide to. Measured on 2026-08-28, 56% of real sessions made that decision
    and 25 to 32% of short ones did, so rules that lived only in Me.md were
    absent from the sessions most likely to need them.

    Two sources, because the two halves have different owners. The personal
    card in Me.md is this person's alone and no update ever touches it. The
    shared card in `System/Agent Rules.md` is the same in every installation
    and arrives with each version, which is the only way an improvement to the
    rules ever reaches anybody else.

    Personal first: an agent should know who it is working for before it reads
    the discipline. These two files are adapters: delete them, regenerate, and
    nothing is lost.
    """
    me = VAULT / "Maps & Manuals/Me.md"
    if not me.exists():
        return []
    personal = read_card(me)
    if not personal:
        # A vault installed before v2.26 has no card, so it would receive every
        # future improvement to the shared rules as nothing at all. Migrating
        # it is safe by construction: the card is inserted above whatever is
        # already there, nothing is deleted, and running it twice does nothing.
        # So it runs itself rather than waiting to be asked, which is what "not
        # optional" has to mean in a vault whose owner is not technical.
        #
        # Never under --check: that runs inside the lint on every save, and a
        # check that writes is not a check.
        if check:
            return list(ENTRY_FILES)
        adopt = SYSTEM / "scripts/adopt_card.py"
        if adopt.exists():
            subprocess.run([sys.executable, str(adopt), "--yes"],
                           capture_output=True, text=True)
            personal = read_card(me)
        if not personal:
            # The migration could not run. Still never overwrite a CLAUDE.md
            # somebody wrote by hand: that is the worst possible way to deliver
            # an update.
            return []
    shared = read_card(SYSTEM / "Agent Rules.md")
    card = personal + ("\n\n" + shared if shared else "")
    # Wikilinks are for Obsidian, which reads Me.md. An agent reads the entry
    # file and opens things by path, so the [[a/b\|b]] form spends characters
    # naming the same note twice and gives the agent nothing it can use.
    card = WIKILINK_RE.sub(lambda w: w.group(1).strip() + ".md", card)

    changed = []
    for name in ENTRY_FILES:
        other = [o for o in ENTRY_FILES if o != name][0]
        # Nothing but the cards. Every section that used to wrap them -- a
        # preamble explaining the generation, an index of the other Maps &
        # Manuals files, a "before you start" -- was either restating the card
        # or had gone stale against it, and it was loaded in every session
        # either way.
        body = f"""# {name}

> This file is {LOADER_MARK} from "Maps & Manuals/Me.md" and "System/Agent Rules.md". Edit those, not this file.

Entry point for agents working in this vault. Identical in content to `{other}`.

{card}
"""
        target = VAULT / name
        if not target.exists() or target.read_text(encoding="utf-8") != body:
            changed.append(name)
            if not check:
                target.write_text(body, encoding="utf-8")
    return changed


def render_calendar_notes() -> str:
    notes = [p for p in sorted((VAULT / "Ideaverse/Calendar").glob("*.md"), reverse=True)
             if p.name != "Calendar.md"]
    if not notes:
        return "*No calendar notes yet.*"
    lines = []
    for p in notes:
        rel = p.relative_to(VAULT).with_suffix("")
        lines.append(f"- {wikilink(str(rel), p.stem)}")
    return "\n".join(lines)



def render_effort_outputs(effort_name: str):
    """The outputs this one project produced, listed inside the project itself.

    A finished analysis that nothing links to is invisible: three council
    verdicts written on 2026-08-04 sat unread for two days because the project
    note did not know they existed. This table is the mechanical half of the
    fix. The other half cannot be generated: an output that concludes something
    has to have its conclusion written into the project note by whoever produced
    it, in the same session.
    """
    def render() -> str:
        base = VAULT / "Ideaverse/Efforts" / effort_name / "Outputs"
        rows = []
        for f in sorted(base.rglob("*"), reverse=True):
            if f.is_dir() or f.name.startswith("."):
                continue
            m = re.match(r"^(\d{4}-\d{2}(?:-\d{2})?)", f.name)
            date = m.group(1) if m else ""
            if f.suffix == ".md":
                rel = f.relative_to(VAULT).with_suffix("")
                cell = wikilink_table(str(rel), f.stem)
                purpose = parse_frontmatter(f).get("summary", "")
            else:
                cell, purpose = f"`{f.name}`", ""
            rows.append(f"| {cell} | {date} | {purpose} |")
        if not rows:
            return "*Nothing produced yet.*"
        return "\n".join(["| Output | Date | What it is |", "|---|---|---|"] + rows)
    return render


def _effort_output_views() -> dict:
    """One generated block per project that has outputs, keyed by its note."""
    views = {}
    efforts = VAULT / "Ideaverse/Efforts"
    if not efforts.is_dir():
        return views
    for d in sorted(efforts.iterdir()):
        if not (d.is_dir() and (d / "Outputs").is_dir()):
            continue
        note = f"Ideaverse/Efforts/{d.name}/{d.name}.md"
        if (VAULT / note).exists():
            views[note] = {"effort-outputs": render_effort_outputs(d.name)}
    return views


VIEWS = {
    "Ideaverse/Efforts/Efforts Index.md": {"efforts-tables": render_efforts_tables},
    "Maps & Manuals/Active Context.md": {"active-efforts": render_active_context_efforts},
    "Ideaverse/Atlas/Atlas Index.md": {"atlas-notes": render_atlas_notes},
    "Ideaverse/Sources/Sources Index.md": {"sources-table": render_sources_table},
    "Ideaverse/Outputs/Outputs Index.md": {"outputs-table": render_outputs_table},
    "Ideaverse/Calendar/Calendar.md": {"calendar-notes": render_calendar_notes},
    "Maps & Manuals/Skill Map.md": {
        "skill-map-workflows": render_skill_map_workflows,
        "skill-map-tools": render_skill_map_tools,
    },
}

VIEWS.update(_effort_output_views())


def apply_views(check: bool) -> int:
    changed = []
    for rel, views in VIEWS.items():
        path = VAULT / rel
        text = path.read_text(encoding="utf-8")
        new_text = text
        for name, renderer in views.items():
            pattern = re.compile(
                rf"(<!-- BEGIN GENERATED: {name} -->)(.*?)(<!-- END GENERATED: {name} -->)",
                re.DOTALL,
            )
            if not pattern.search(new_text):
                print(f"ERROR: markers for view '{name}' not found in {rel}")
                return 2
            body = renderer()
            new_text = pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", new_text)
        if new_text != text:
            changed.append(rel)
            if not check:
                path.write_text(new_text, encoding="utf-8")
    changed += generate_loaders(check)
    changed += generate_entry_files(check)
    if check and changed:
        print("Views out of date (run: python3 scripts/build_views.py):")
        for c in changed:
            print(f"  {c}")
        return 1
    for c in changed:
        print(f"regenerated: {c}")
    if not changed:
        print("all views up to date")
    return 0


if __name__ == "__main__":
    sys.exit(apply_views(check="--check" in sys.argv))
