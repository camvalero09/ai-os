#!/usr/bin/env python3
"""
Vault lint script for the vault.

Errors (exit 1):
  1. Bare wikilinks: [[Note Name]] without a full vault-relative path.
  2. Missing summary field on Atlas and Effort notes.
  3. Broken wikilinks pointing to files that do not exist.
  4. Entry-point drift: CLAUDE.md and AGENTS.md differ in content.
  5. Unknown status values (vocabulary lives in Skills/Data Models/YAML Metadata Standard.md).
  6. Generated views out of sync with frontmatter (build_views.py --check).

  7. Unescaped pipes in table wikilinks (Obsidian drops those graph edges).
  8. Orphan notes: every note must have at least one inbound wikilink
     (Archive, Inbox, and entry points excluded).
  9. Stray instruction files: any CLAUDE.md, AGENTS.md, GEMINI.md or equivalent
     other than the two at the vault root. Agents load nested ones silently.
 10. Frontmatter that does not parse (a note then reads as having no settings).

Warnings (reported, exit 0):
  - Onboarding left half-finished, or the config and the maps disagreeing
    about who owns this vault.
  - Permissions granted once via "always allow" and never surfaced since.
  - System work that is stranded: uncommitted, unpushed, or untagged.
  - Active efforts with no update in 30+ days.

Ignores content inside code blocks and inline code to avoid false positives.
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
ATLAS_DIR = VAULT / "Ideaverse/Atlas"
EFFORTS_DIR = VAULT / "Ideaverse/Efforts"
# Records that describe the authoring repository itself (its plan, its
# maintainer rules, its review artifacts), not the vault an installation
# lives in. An installed checkout still carries them under System/, since the
# whole repository is cloned there, but no vault note is ever meant to link
# to them. Listed explicitly rather than inferred, so adding one is a
# one-line decision instead of a heuristic that could also hide a real
# orphaned note.
AUTHORING_ONLY_RECORDS = {"IMPLEMENTATION_PLAN.md", "MAINTAINER_RULES.md", "T03_RULES_PROPOSAL.md"}
BARE_WIKILINK_ALLOWLIST = {"AGENTS", "CLAUDE"}
ALLOWED_STATUSES = {
    "raw", "draft", "active", "stable", "needs_review",
    "processed", "archived", "deprecated", "closed",
}
STALE_DAYS = 30
IGNORED_DIR_NAMES = {".git", ".obsidian", "node_modules"}


def is_host_managed_worktree(path: Path) -> bool:
    """Whether a path belongs to a host's separate working copy."""
    roots = (VAULT / ".claude/worktrees", VAULT / ".agents/worktrees")
    return any(root == path or root in path.parents for root in roots)


def get_all_md_files():
    """Every live note in this vault.

    Excludes the system's `template/` folder: those files exist only to seed a
    brand new vault, and counting them here would double every entry point and
    report install-time scaffolding as orphaned notes. Excludes
    AUTHORING_ONLY_RECORDS for the same reason: they describe the authoring
    repository, not the vault, and an installed checkout has nowhere for a
    vault note to link them from. Host-managed worktrees are complete working
    copies, not live vault content; counting them duplicates notes and loads
    nested instruction files.
    """
    seed = SYSTEM / "template"
    authoring_only = {SYSTEM / name for name in AUTHORING_ONLY_RECORDS}
    return [f for f in VAULT.rglob("*.md")
            if not IGNORED_DIR_NAMES.intersection(f.parts)
            and seed not in f.parents
            and not is_host_managed_worktree(f)
            and f not in authoring_only]


def strip_code(content):
    """Remove fenced code blocks and inline code before scanning."""
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    content = re.sub(r'~~~.*?~~~', '', content, flags=re.DOTALL)
    content = re.sub(r'`[^`\n]+`', '', content)
    return content


def parse_frontmatter(path):
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"')
    return fm


def check_bare_wikilinks(files):
    issues = []
    bare_pattern = re.compile(r'\[\[([^|\]/\\\[]+)\]\]')
    for f in files:
        content = strip_code(f.read_text(encoding="utf-8"))
        for match in bare_pattern.finditer(content):
            note_name = match.group(1).strip()
            if note_name not in BARE_WIKILINK_ALLOWLIST:
                issues.append(f"  {f.relative_to(VAULT)}: [[{note_name}]]")
    return issues


def check_missing_summary(files):
    issues = []
    yaml_pattern = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
    for f in files:
        is_atlas = ATLAS_DIR in f.parents
        is_effort = EFFORTS_DIR in f.parents
        if not (is_atlas or is_effort):
            continue
        if f.name.endswith("Index.md"):
            continue
        content = f.read_text(encoding="utf-8")
        yaml_match = yaml_pattern.match(content)
        if yaml_match:
            if "summary:" not in yaml_match.group(1):
                issues.append(f"  {f.relative_to(VAULT)}")
        else:
            issues.append(f"  {f.relative_to(VAULT)} (no YAML frontmatter)")
    return issues


def check_frontmatter_parses(files):
    """A note that opens with --- must have a settings block that actually parses.

    Added after a shipped file opened `---`, put a paragraph before the first
    field, and closed the block. Obsidian saw no settings, the vault's own parser
    saw no settings, and every check passed, because the only check that looks at
    settings content is scoped to two folders. A file can be broken anywhere else
    and be reported as clean.
    """
    issues = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        end = text.find("\n---", 4)
        if end == -1:
            issues.append(f"  {f.relative_to(VAULT)}: opens with --- and never closes it")
            continue
        block = text[4:end]
        fields = [ln for ln in block.splitlines()
                  if re.match(r"^[A-Za-z_]+:", ln)]
        if not fields:
            issues.append(f"  {f.relative_to(VAULT)}: the block at the top holds no settings at all")
            continue
        stray = [ln for ln in block.splitlines()
                 if ln.strip() and not re.match(r"^[A-Za-z_]+:", ln) and not ln.startswith((" ", "-", "\t"))]
        if stray:
            issues.append(f"  {f.relative_to(VAULT)}: line {stray[0][:40]!r} is not a setting")
    return issues


def build_file_index(files):
    return {str(f.relative_to(VAULT).with_suffix("")) for f in files}


def check_broken_wikilinks(files, file_index):
    issues = []
    link_pattern = re.compile(r'\[\[([^|\]\\\[]+)(?:\\?\|[^\]]+)?\]\]')
    for f in files:
        content = strip_code(f.read_text(encoding="utf-8"))
        for match in link_pattern.finditer(content):
            path = match.group(1).strip().rstrip("\\")
            if "/" not in path:
                continue
            path = path.lstrip("/")
            if path not in file_index:
                issues.append(f"  {f.relative_to(VAULT)}: [[{path}]]")
    return issues


def check_table_pipes(files):
    """Wikilinks inside markdown tables must escape the pipe ([[path\\|display]])
    or Obsidian drops the link (no graph edge, broken cell)."""
    issues = []
    pattern = re.compile(r'\[\[[^\]|\\]+\|')
    for f in files:
        for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if ln.lstrip().startswith("|") and pattern.search(ln):
                issues.append(f"  {f.relative_to(VAULT)}, line {i}")
    return issues


def check_entry_points():
    """CLAUDE.md and AGENTS.md must be identical after normalizing their names."""
    missing = [n for n in ("CLAUDE.md", "AGENTS.md") if not (VAULT / n).exists()]
    if missing:
        return [f"  missing entry point: {n}" for n in missing]

    def normalized(name):
        text = (VAULT / name).read_text(encoding="utf-8")
        return text.replace("CLAUDE.md", "ENTRY").replace("AGENTS.md", "ENTRY")
    if normalized("CLAUDE.md") != normalized("AGENTS.md"):
        return ["  CLAUDE.md and AGENTS.md"]
    return []


def check_stray_instruction_files():
    """No instruction file may exist other than the two known entry points.

    Coding agents read instruction files out of the folder they are working in,
    and most of them read nested ones too: a `CLAUDE.md` sitting in a subfolder
    is loaded as live instructions on top of the root one, and Codex does the
    same with `AGENTS.md`. So any file with one of these names, anywhere in the
    vault, silently becomes rules that no one wrote and no one reviewed.

    It does not take a hostile agent for one to appear. A downloaded folder, a
    synced Drive file, an example repository someone shares, an agent tidying up
    after itself: all of them can drop one in. This is an error rather than a
    warning because the failure is invisible by construction. The whole point of
    an instruction file is that it takes effect without anyone reading it.
    """
    known = {"CLAUDE.md", "AGENTS.md"}
    # Names that agents in common use load automatically. Anything here that is
    # not one of the two root entry points is an override channel.
    watched = known | {
        "GEMINI.md", "CONVENTIONS.md", ".cursorrules", ".windsurfrules",
        ".aider.conf.yml", "copilot-instructions.md",
    }
    problems = []
    for path in VAULT.rglob("*"):
        if (IGNORED_DIR_NAMES.intersection(path.parts)
                or is_host_managed_worktree(path)
                or not path.is_file()):
            continue
        # System/ is the shared system's own repository and carries its own
        # entry points legitimately. It is read-only here and updated by tag.
        if SYSTEM != VAULT and SYSTEM in path.parents:
            continue
        if path.name not in watched:
            continue
        rel = path.relative_to(VAULT)
        if str(rel) in known:
            continue
        problems.append(f"  {rel}")
    return problems


def warn_local_permission_grants():
    """Surface permissions granted once in a dialog and never seen again.

    Clicking "always allow" writes `.claude/settings.local.json`. Nothing ever
    shows that file again: updates replace `.claude/settings.json` and leave it
    untouched, so a permission granted during a confusing moment on the first
    evening still applies a year later. Reported so the choice is at least
    visible, never blocking, because every entry in it was allowed on purpose.
    """
    import json
    path = VAULT / ".claude/settings.local.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [f"  {path.relative_to(VAULT)} exists but is not readable as settings."]
    allowed = (data.get("permissions") or {}).get("allow") or []
    if not allowed:
        return []
    out = [
        f"  {len(allowed)} permission(s) were granted by clicking 'always allow', and they "
        "stay granted through every update:"
    ]
    out.extend(f"      {entry}" for entry in allowed[:8])
    if len(allowed) > 8:
        out.append(f"      and {len(allowed) - 8} more")
    out.append(
        "      Delete .claude/settings.local.json to be asked again. The shared list "
        "in .claude/settings.json is unaffected."
    )
    return out


def check_append_only_files(files):
    """A file that records history may gain lines. It may never lose one.

    The rule saying so has existed since 2026-08-02 and was enforced by nothing.
    Four days later an agent rewrote 33 past log entries to use folder names
    that did not exist when they were written: every one read as authoritative
    and every one was false. Thirty-three were reverted by hand.

    This is the mechanical half. It compares each protected file against the
    last commit and fails if any line present there is gone now. Reordering is
    allowed to pass, since a moved line is still present; that is the deliberate
    limit of a cheap check, and it catches the failure that actually happened.

    Blocking, because a falsified history cannot be spotted by reading it.
    """
    protected = [f for f in files
                 if f.name == "Project_log.md" or f.name == "Agent Log.md"]
    problems = []
    for f in protected:
        rel = f.relative_to(VAULT).as_posix()
        before = _git(VAULT, "show", f"HEAD:{rel}")
        if not before:
            continue  # new file, nothing to lose yet
        # A link whose target moved has to be repointed or it breaks, and that
        # is not a change to what the entry says. Comparing with link targets
        # stripped keeps the check on the words while allowing link repair.
        def bare(line):
            return re.sub(r"\[\[[^\]]*\]\]", "[[]]", line)

        def body(text):
            """The log itself, without the settings block at the top.

            That block is a settings block, not history: `updated:` is supposed
            to change every time the file is touched, and the old value is
            genuinely gone afterwards. Counting it as a lost line blocked a
            commit on 2026-08-20 that had removed no row at all, which is worse
            than not checking, because the person hitting it cannot tell a real
            falsified history from this.
            """
            lines = text.splitlines()
            if lines and lines[0].strip() == "---":
                for i in range(1, len(lines)):
                    if lines[i].strip() == "---":
                        return lines[i + 1:]
            return lines

        def protected_region(text):
            """The part of the file that may never lose a line.

            The Agent Log has two halves and only the first is history. Section
            2 holds candidate rules that Weekly Maintenance is supposed to
            delete once they are promoted or turn 90 days old, so protecting it
            stops the loop it belongs to: on 2026-08-29 it held 20 entries
            proposing a rule and had promoted none.
            """
            lines = body(text)
            if f.name == "Agent Log.md":
                for i, ln in enumerate(lines):
                    if ln.startswith("## Section 2"):
                        return lines[:i]
            return lines

        now = {bare(ln) for ln in protected_region(f.read_text(encoding="utf-8"))}
        lost = [ln for ln in protected_region(before)
                if ln.strip() and bare(ln) not in now]
        if lost:
            problems.append(f"  {rel}: {len(lost)} line(s) removed")
            for ln in lost[:3]:
                problems.append(f"      {ln[:100]}")
    return problems


LOG_ENTRY_WORD_CAP = 120


def check_new_log_entries_length(files):
    """A new Agent Log Section 1 entry must fit the cap the log itself sets.

    The cap was written into the log's own format block on 2026-08-03 and
    enforced by nothing. On 2026-08-29, 46 of 60 entries were over it, including
    one written that day by the agent adding this check, and including the entry
    that introduced the cap. Prose said it for 26 days and nothing changed.

    Blocking, and only on entries this commit adds: the fix is to trim a
    paragraph you just wrote, which is seconds of work and entirely yours. Old
    entries are left alone on purpose, since rewriting them would falsify a
    record that was accurate when written.
    """
    log = [f for f in files if f.name == "Agent Log.md"]
    if not log:
        return []
    f = log[0]
    rel = f.relative_to(VAULT).as_posix()

    def section_one_entries(text):
        if "## Section 1" not in text:
            return {}
        s1 = text[text.index("## Section 1"):]
        if "## Section 2" in s1:
            s1 = s1[:s1.index("## Section 2")]
        out = {}
        for block in re.split(r"(?m)^### ", s1)[1:]:
            out[block.split("\n")[0].strip()] = len(block.split())
        return out

    before = section_one_entries(_git(VAULT, "show", f"HEAD:{rel}"))
    now = section_one_entries(f.read_text(encoding="utf-8"))
    problems = []
    for title, words in now.items():
        if title in before or words <= LOG_ENTRY_WORD_CAP:
            continue
        problems.append(f"  {rel}: new entry is {words} words, cap is "
                        f"{LOG_ENTRY_WORD_CAP}")
        problems.append(f"      {title[:80]}")
    if problems:
        problems.append("      Trim **Why**. It is the field that inflates, and "
                        "the reasoning belongs in Rule Origins or the changelog.")
    return problems


def warn_tags_without_changelog():
    """Warn when a released version has no entry saying what it changed.

    The changelog is what the update notice shows an adopter deciding whether to
    accept a version, so a tag without one ships a decision nobody can make. Six
    versions shipped that way before 2026-08-05, and v2.12 to v2.14 did it again
    on 2026-08-28, found only because someone went looking.
    """
    repo = SYSTEM if (SYSTEM / "CHANGELOG.md").is_file() else None
    if repo is None:
        return []
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    tags = [t for t in _git(repo, "tag", "-l").splitlines() if t.strip()]
    missing = [t for t in tags if f"## {t} " not in text and f"## {t}\n" not in text]
    if not missing:
        return []
    shown = ", ".join(sorted(missing)[:6])
    more = f" and {len(missing) - 6} more" if len(missing) > 6 else ""
    return [f"{len(missing)} released version(s) have no changelog entry: "
            f"{shown}{more}. The update notice shows that file to whoever is "
            f"deciding whether to install."]


def warn_stale_questions(files):
    """A question that has sat open for a month is not being worked on.

    Questions used to live in prose, where they were opened by anyone and closed
    by nobody: one about a contract clause stayed listed as blocking for two days
    after it had been answered in another session, and an agent repeated it back
    as a blocker. The table makes closing possible; this makes forgetting visible.

    Reported only, and only when asked for. Nothing here should raise these in a
    session that was about something else. That behaviour was switched off on
    2026-08-06 for being exactly as annoying as it sounds.
    """
    if not EFFORTS_DIR.is_dir():
        return []
    row = re.compile(r"^\|([^|]+)\|([^|]*)\|([^|]*)\|")
    today = date.today()
    out = []
    for d in sorted(EFFORTS_DIR.iterdir()):
        note = d / f"{d.name}.md"
        if not (d.is_dir() and note.exists()):
            continue
        body = note.read_text(encoding="utf-8")
        if "## Open questions" not in body:
            continue
        section = body.split("## Open questions", 1)[1].split("\n---", 1)[0]
        for line in section.splitlines():
            m = row.match(line.strip())
            if not m:
                continue
            q, opened, status = (g.strip() for g in m.groups())
            if "open" not in status.lower() or "closed" in status.lower():
                continue
            try:
                age = (today - date.fromisoformat(opened.strip("* "))).days
            except ValueError:
                continue
            if age >= STALE_DAYS:
                out.append(f"  {d.name}: \"{q[:70]}\" has been open {age} days")
    return out


def check_status_vocabulary(files):
    issues = []
    for f in files:
        fm = parse_frontmatter(f)
        status = fm.get("status")
        if status and status not in ALLOWED_STATUSES:
            issues.append(f"  {f.relative_to(VAULT)}: '{status}'")
    return issues


# Both Anthropic and OpenAI publish the same floor for the skill list an agent
# holds in context at startup: 2% of the context window, or 8,000 characters
# when the window is unknown. Only the name and description of each skill count
# toward it; the body loads later, when a skill is actually chosen. The number
# is a vendor constant, so it lives here with its source rather than inline.
#   https://learn.chatgpt.com/docs/build-skills
#   https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
SKILL_LIST_BUDGET_CHARS = 8000
SKILL_LIST_WARN_AT = 0.80


def warn_skill_list_budget():
    """Warn before the skill list outgrows what agents load at startup.

    Over the budget, an agent may not see every skill, and the ones it misses
    fail silently: nothing reports a skill that was never offered.
    """
    skills_dir = VAULT / ".claude/skills"
    if not skills_dir.is_dir():
        return []
    total = 0
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        fm = parse_frontmatter(skill_md)
        total += len(fm.get("name", "")) + len(fm.get("description", ""))
    if total < SKILL_LIST_BUDGET_CHARS * SKILL_LIST_WARN_AT:
        return []
    pct = 100 * total / SKILL_LIST_BUDGET_CHARS
    verdict = "over" if total > SKILL_LIST_BUDGET_CHARS else "close to"
    return [f"Skill list is {pct:.0f}% of what agents load at startup "
            f"({total:,} of {SKILL_LIST_BUDGET_CHARS:,} characters, {verdict} the limit). "
            f"Past it, some skills are never offered. Shorten the longest "
            f"`summary:` fields in Skills/."]


# Anthropic, on the file agents load automatically: "Target under 200 lines per
# CLAUDE.md file. Longer files consume more context and reduce adherence." It is
# the only published size number for an entry file; OpenAI gives none.
ENTRY_FILE_BUDGET_LINES = 200
ENTRY_FILE_WARN_AT = 0.80


def warn_entry_file_budget():
    """Warn before the always-loaded rules file grows back.

    Every rule added to it will have a good reason, which is exactly why it
    grows. On 2026-08-29 it was cut from 132 lines to 114 by deleting a wrapper
    that restated the rules it wrapped; without something watching, that returns.
    """
    entry = VAULT / "CLAUDE.md"
    if not entry.is_file():
        return []
    lines = entry.read_text(encoding="utf-8").count("\n")
    if lines < ENTRY_FILE_BUDGET_LINES * ENTRY_FILE_WARN_AT:
        return []
    pct = 100 * lines / ENTRY_FILE_BUDGET_LINES
    verdict = "over" if lines > ENTRY_FILE_BUDGET_LINES else "close to"
    return [f"CLAUDE.md is {lines} lines, {pct:.0f}% of the 200 Anthropic "
            f"targets ({verdict} it). Past it, adherence drops. The card in "
            f"Maps & Manuals/Me.md is the only thing in there: shorten it, or "
            f"move a section that has become a procedure into a skill."]


def check_credentials_are_safe():
    """Passwords must not be in the backup, and blocking the save is the point.

    A vault seeded before the secret-patterns fix had no .gitignore, so its
    first save would have committed its own credentials. Nothing told the owner
    then and nothing would tell them now, which is why this is an error rather
    than a note: the save it blocks is the one that would publish the token.
    """
    try:
        from check_credentials import check, vault_root
    except ImportError:
        return []
    vault = vault_root()
    if vault is None:
        return []
    return ["  " + line for line in check(vault)]


def check_shared_rules_are_impersonal():
    """The one file every installation loads must name nobody.

    Delegated to check_shared_rules.py so the same check can run in the system
    repository, where there is no vault to lint but where the commit that would
    publish the leak is actually made.
    """
    try:
        from check_shared_rules import SHARED_RULES, check
    except ImportError:
        return []
    if not SHARED_RULES.exists():
        return []
    return ["  " + line for line in check()]


def check_views_in_sync():
    result = subprocess.run(
        [sys.executable, str(SYSTEM / "scripts/build_views.py"), "--check"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return ["  " + line for line in result.stdout.strip().splitlines()]
    return []


def _git(repo: Path, *args) -> str:
    """Run one git command in `repo`, returning stdout or "" if it cannot."""
    try:
        r = subprocess.run(["git", "-C", str(repo), *args],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def warn_card_blanks():
    """The migration writes the card; only the owner can fill it in.

    `adopt_card.py` runs itself during an update, so a vault gets the shape
    without anyone deciding to. What it cannot do is invent who the owner is,
    so it leaves marked blanks. A blank left in place means every session
    starts by reading TO FILL IN as though it were a fact about the person.
    """
    me = VAULT / "Maps & Manuals/Me.md"
    if not me.is_file():
        return []
    card = re.search(r"<!-- BEGIN CARD -->\n(.*?)<!-- END CARD -->",
                     me.read_text(encoding="utf-8"), re.DOTALL)
    if not card:
        return []
    blanks = card.group(1).count("TO FILL IN")
    if not blanks:
        return []
    return [f"Maps & Manuals/Me.md: the card has {blanks} blank(s) still marked "
            "TO FILL IN, and agents read the card in every session. Answer them "
            "in your own words, then: python3 System/scripts/build_views.py"]


def warn_system_state():
    """Catch system work that is stranded and will never reach anyone.

    An improvement to a shared skill is worth nothing until it is committed,
    tagged and pushed. Two ways it silently is not:

    1. It was made inside this vault's System/, which is a read-only checkout
       pinned to a version tag. The edit reaches nobody and blocks the next
       update, which refuses to run over local changes.
    2. It was made in the authoring copy but never pushed, or pushed without a
       tag, so no vault can install it.

    Reported on every commit because that is when the author is present. Never
    blocking: stranded work is a mistake, not a broken vault.
    """
    warnings = []

    installed = SYSTEM if SYSTEM != VAULT else None

    # An update nobody knows about is an update nobody installs. This reads only
    # what the last fetch already downloaded, so it never touches the network and
    # cannot make saving slow or fail offline.
    if installed and (installed / ".git").exists():
        here = _git(installed, "describe", "--tags", "--exact-match") or _git(
            installed, "describe", "--tags")
        known = [t for t in _git(installed, "tag", "--sort=-v:refname").splitlines() if t]
        if known and here and known[0] != here:
            warnings.append(
                f"  A newer version of the system is available: {known[0]}, and this vault is on {here}. "
                "Ask your agent to update the system, and it will show you what changed first."
            )

    # Everything above compares against tags already downloaded. If nothing has
    # fetched in a long time, "no newer version" means "nothing has looked",
    # and those are indistinguishable to the reader. Say which one it is.
    if installed and (installed / ".git").exists():
        import time as _time
        marks = [installed / ".git" / n for n in ("FETCH_HEAD", "HEAD")]
        stamps = [p.stat().st_mtime for p in marks if p.exists()]
        if stamps:
            days = int((_time.time() - max(stamps)) / 86400)
            if days >= 10:
                warnings.append(
                    f"  Nobody has checked for a system update in {days} days, so the version "
                    "check above is only as current as that. Say weekly maintenance to your "
                    "agent, which is the one thing that looks."
                )

    if installed and (installed / ".git").exists():
        dirty = _git(installed, "status", "--porcelain")
        if dirty:
            n = len(dirty.splitlines())
            warnings.append(
                f"  System/ has {n} local change(s). That folder is a read-only copy of the "
                "shared system: the change reaches nobody and the next update will refuse to run."
            )
            for line in dirty.splitlines()[:5]:
                warnings.append(f"      {line}")
            warnings.append(
                "      Make the change in the authoring copy instead, then commit, tag and push there."
            )

    authoring = vault_config().get("system_authoring_path")
    if not authoring:
        return warnings
    repo = Path(authoring).expanduser()
    if not (repo / ".git").exists():
        warnings.append(f"  system_authoring_path is set to {repo}, which is not a git repository.")
        return warnings

    if _git(repo, "status", "--porcelain"):
        warnings.append(f"  Uncommitted system work in {repo.name}. Commit it or it reaches nobody.")

    unpushed = _git(repo, "log", "--oneline", "@{upstream}..HEAD")
    if unpushed:
        warnings.append(
            f"  {len(unpushed.splitlines())} unpushed commit(s) in {repo.name}. "
            "Push, or no other vault can ever install this."
        )

    # Commits after the newest tag are real but uninstallable: vaults move by tag.
    newest = _git(repo, "describe", "--tags", "--abbrev=0")
    if newest:
        since = _git(repo, "log", "--oneline", f"{newest}..HEAD")
        if since:
            warnings.append(
                f"  {len(since.splitlines())} commit(s) in {repo.name} since {newest}, with no newer tag. "
                f"Vaults install tags, so this work is invisible until you cut one."
            )
    return warnings


def vault_config() -> dict:
    """Per-vault settings from vault.config.json at the vault root."""
    import json
    path = VAULT / "vault.config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


ONBOARDING_STAGES = {
    1: "who you are, into Me.md and the config",
    2: "check the machinery works",
    3: "your first real project",
    4: "connect Google, Discord, whatever you use",
    5: "prove it works in a fresh session",
}

# Files that carry a placeholder until onboarding has been through them. The
# text is what the shipped copy says; onboarding replaces it with a real date.
ONBOARDING_PLACEHOLDER = "not yet reviewed by this vault's owner"


def warn_onboarding_state():
    """Report where onboarding stopped, and any disagreement about who owns this.

    Two failures, both found by giving a cold agent a half-finished vault.

    Onboarding is five stages over several sittings and its own instructions say
    not to do it all at once, but every file it touches said only "delete this
    block once onboarding is done". There was no way to record stopping after
    stage two, so an agent picking it up a week later had to guess, and guessed
    wrong. `onboarding_stage` in the config is where that is written down now.

    The second is worse because it is silent: the config can say the owner is
    one person while Me.md, Active Context and the maps still carry the shipped
    placeholder. Both are then true at once and agents believe whichever they
    read first.
    """
    if not _is_installed_vault():
        return []
    cfg = vault_config()
    owner = (cfg.get("owner_name") or "").strip()
    stage = cfg.get("onboarding_stage")

    stale = []
    for name in ("Me.md", "Active Context.md", "Vault Map.md", "Skill Map.md"):
        path = VAULT / "Maps & Manuals" / name
        if path.exists() and ONBOARDING_PLACEHOLDER in path.read_text(encoding="utf-8"):
            stale.append(name)

    if not owner:
        if stale:
            return [
                "  This vault has no owner yet. Ask your agent to onboard you and it "
                "walks you through it, a stage at a time."
            ]
        return []

    warnings = []
    if isinstance(stage, int) and stage < 5:
        nxt = ONBOARDING_STAGES.get(stage + 1, "")
        warnings.append(
            f"  Onboarding stopped after stage {stage} of 5. Next is {nxt}. "
            "Say 'continue onboarding' when you have twenty minutes."
        )
    elif stage is None:
        warnings.append(
            "  onboarding_stage is missing from vault.config.json, so nothing records "
            "how far setup got. Set it to the last stage finished, or to 5 if it is done."
        )

    if stale:
        warnings.append(
            f"  {owner} owns this vault according to vault.config.json, but "
            f"{', '.join(stale)} still say nobody has reviewed them. Whichever an agent "
            "reads first is what it believes."
        )
    return warnings


def warn_stale_efforts():
    warnings = []
    if not EFFORTS_DIR.is_dir():
        return warnings
    for d in sorted(EFFORTS_DIR.iterdir()):
        main = d / f"{d.name}.md"
        if not (d.is_dir() and main.exists()):
            continue
        fm = parse_frontmatter(main)
        if fm.get("status") != "active":
            continue
        try:
            age = (date.today() - date.fromisoformat(fm.get("updated", ""))).days
        except ValueError:
            warnings.append(f"  {d.name}: no valid 'updated' date")
            continue
        if age > STALE_DAYS:
            warnings.append(f"  {d.name}: active but not updated in {age} days")
    return warnings


MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
ISO_DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
LONG_DATE = re.compile(r"\b(\d{1,2})\s+([A-Z][a-z]+)\s+(20\d{2})\b")
AS_OF = re.compile(r"as of\s+(?:the\s+)?([^.,;)\n]{4,30})", re.I)
SNAPSHOT_MAX_AGE = 45


def _dates_in(text):
    """Every parseable date in a string, as date objects."""
    found = []
    for y, m, d in ISO_DATE.findall(text):
        try:
            found.append(date(int(y), int(m), int(d)))
        except ValueError:
            pass
    for d, mon, y in LONG_DATE.findall(text):
        month = MONTHS.get(mon.lower())
        if month:
            try:
                found.append(date(int(y), month, int(d)))
            except ValueError:
                pass
    return found


def warn_expired_content(files):
    """Content whose meaning has expired, as opposed to a note nobody edited.

    Staleness by edit date already has a check. This is the other kind: a note
    that was accurate when written and quietly became false as time passed. The
    agent still reads it as current, because nothing about the file changed.

    Two signals, both low-noise:

      * A date in the past inside a `next:` field. `next:` is forward-looking by
        definition, so a past date there means the action is due or overdue and
        the generated views are telling every agent otherwise.
      * An "as of <date>" claim older than SNAPSHOT_MAX_AGE days. Labelling a
        snapshot is good practice; leaving it to age silently is not.

    Deliberately not flagged: past dates in prose. "Signed June 2026" is a fact,
    not an expiry, and flagging those would bury the real findings.
    """
    today = date.today()
    warnings = []
    for f in files:
        rel = f.relative_to(VAULT)
        fm = parse_frontmatter(f)

        nxt = fm.get("next", "")
        overdue = sorted(d for d in _dates_in(nxt) if d < today)
        if overdue:
            days = (today - overdue[0]).days
            warnings.append(
                f"  {rel}: next action references {overdue[0].isoformat()} "
                f"({days}d past); may be due or done"
            )

        try:
            body = strip_code(f.read_text(encoding="utf-8"))
        except OSError:
            continue
        for m in AS_OF.finditer(body):
            claimed = sorted(_dates_in(m.group(1)))
            if not claimed:
                continue
            age = (today - claimed[-1]).days
            if age > SNAPSHOT_MAX_AGE:
                warnings.append(
                    f"  {rel}: \"as of {claimed[-1].isoformat()}\" is {age}d old; "
                    "re-verify or relabel as historical"
                )
                break  # one per file is enough to prompt a look
    return warnings


def warn_effort_names_in_skills(files):
    """Skill notes should be reusable; naming a specific effort means they are not.

    This is how the Layer 1 boundary erodes: a generic-looking skill file quietly
    accumulates one project's details until it only works for that project.

    Warning, not an error, because some cross-references are deliberate. A skill
    documenting a shared account legitimately names the effort that owns it, to
    state a safety boundary. Such a note opts out with `effort_refs: intentional`
    in its frontmatter.

    Known gap: this matches full effort names and wikilinks into Efforts/, so
    abbreviations a folder name does not contain (an acronym for a longer effort name)
    slip through. Catching those needs an alias list nobody will maintain.
    """
    if not EFFORTS_DIR.is_dir():
        return []
    effort_names = sorted(
        d.name for d in EFFORTS_DIR.iterdir()
        if d.is_dir() and (d / f"{d.name}.md").exists()
    )
    if not effort_names:
        return []

    link_re = re.compile(r"\[\[Ideaverse/Efforts/([^|\]\\]+)")
    warnings = []
    for f in files:
        if not str(f.relative_to(VAULT)).startswith("Skills/"):
            continue
        declared = parse_frontmatter(f).get("effort_refs", "")
        if declared.split("#")[0].strip() == "intentional":
            continue
        body = strip_code(f.read_text(encoding="utf-8"))
        hits = {}
        for name in effort_names:
            n = len(re.findall(re.escape(name), body, re.I))
            if n:
                hits[name] = n
        for m in link_re.finditer(body):
            target = m.group(1).split("/")[0]
            if target in effort_names:  # skip the Efforts Index hub itself
                hits.setdefault(target, 0)
        if hits:
            detail = ", ".join(f"{k} x{v}" if v else k for k, v in sorted(hits.items()))
            warnings.append(
                f"  {f.relative_to(VAULT)}: names specific effort(s): {detail}"
            )
    return warnings


def check_orphans(files):
    link_re = re.compile(r'\[\[([^|\]\\\[]+)(?:\\?\|[^\]]+)?\]\]')
    noext = {str(f.relative_to(VAULT))[:-3] for f in files}
    inbound = set()
    for f in files:
        src = str(f.relative_to(VAULT))[:-3]
        for m in link_re.finditer(strip_code(f.read_text(encoding="utf-8"))):
            tgt = m.group(1).strip().rstrip("\\")
            if tgt in noext and tgt != src:
                inbound.add(tgt)
    skip_names = {"CLAUDE", "AGENTS", "README"}
    warnings = []
    for n in sorted(noext - inbound):
        # Private/ is deliberately unreachable: nothing may link to it, or agents
        # would follow the link and turn one session's observation into vault canon.
        if n.startswith((".claude/", ".agents/", "Ideaverse/Archive/",
                         "Ideaverse/Inbox/", "Private/")) or n.split("/")[-1] in skip_names:
            continue
        warnings.append(f"  {n}")
    return warnings


def _is_installed_vault() -> bool:
    """Whether this is somebody's vault rather than the bare system repository.

    The system repository has skills and scripts but no owner: no entry points,
    no Ideaverse, no Maps & Manuals. Checks about a vault's structure cannot
    mean anything there, so they are skipped rather than crashing or reporting
    absences as faults.
    """
    return (VAULT / "Maps & Manuals").is_dir() and (VAULT / "Ideaverse").is_dir()


def main():
    """Report what is wrong, in words the vault's owner actually uses.

    The person reading this is not a developer. A check named "unescaped pipe in
    table wikilink" tells them nothing they can act on, so each problem is named
    for what it means and followed by how to fix it. Passing checks are counted
    rather than listed: a wall of OK trains people to skim past the one failure.
    """
    files = get_all_md_files()
    installed = _is_installed_vault()
    file_index = build_file_index(files)

    print("Vault check")
    print("=" * 60)
    if installed:
        print(f"Checked {len(files)} notes.\n")
    else:
        print(f"Checked {len(files)} notes in the system itself, so the checks "
              f"about somebody's vault are skipped.\n")

    # (plain name, what to do about it, issues)
    checks = [
        ("A link is written the short way",
         "Links need the full path, like [[Maps & Manuals/Me|Me]]. Written short, "
         "Obsidian cannot follow them and the note goes missing from the graph.",
         check_bare_wikilinks(files)),
        ("A note's settings block is broken",
         "A note that starts with `---` must hold real settings between the markers, one "
         "`name: value` per line, nothing else. Broken, every tool reads the note as having "
         "no settings at all and says nothing.",
         check_frontmatter_parses(files)),
        ("A note is missing its one-line summary",
         "Every Atlas and Effort note needs a `summary:` line at the top. It is what "
         "an agent reads to decide whether to open the note at all.",
         check_missing_summary(files)),
        ("A link inside a table will break",
         "Inside a table, the bar in a link has to be written `\\|` instead of `|`. "
         "Otherwise the table swallows it and the link disappears.",
         check_table_pipes(files)),
        ("A note has a status the vault does not recognise",
         "Allowed values: " + ", ".join(sorted(ALLOWED_STATUSES)) + ".",
         check_status_vocabulary(files)),
        ("This vault's passwords are not being kept out of its backup",
         "Git history is permanent: a credential that reaches it is public for good, "
         "even after the file is deleted. Each line above names the command that "
         "fixes it. Reissuing a token is free and instant; treat any credential that "
         "reached a commit as compromised.",
         check_credentials_are_safe()),
        ("The shared rules file names somebody",
         "System/Agent Rules.md ships to every installation and a published version "
         "can never be amended. Move the detail into the owner's own card in "
         "Maps & Manuals/Me.md, which no update ever reads.",
         check_shared_rules_are_impersonal()),
    ]
    if installed:
        # A shared skill may point at Me.md or the Efforts Index, which exist in
        # every vault but not in the system repository on its own. Those links
        # only resolve against a real installation.
        checks += [
            ("A link points at something that does not exist",
             "Either the note was renamed or moved, or the link has a typo. Fix the "
             "link rather than recreating the note.",
             check_broken_wikilinks(files, file_index)),
            ("The two entry-point files have drifted apart",
             "CLAUDE.md and AGENTS.md must say the same thing, so every agent reads "
             "the same instructions. Copy one over the other.",
             check_entry_points()),
            ("The index tables are out of date",
             "Do not edit those tables by hand. Run: python3 System/scripts/build_views.py",
             check_views_in_sync()),
            ("A note has nothing linking to it",
             "It exists but nothing points at it, so it will never be found. Add a link "
             "from the effort or hub it belongs to.",
             check_orphans(files)),
            ("A record of what happened lost a line",
             "Project logs and Agent Log Section 1 only ever grow. Add a new line "
             "correcting an old one; never edit or delete it. A rewritten history "
             "reads as true, which is what makes it worse than a missing one. "
             "Section 2 is the exception: its entries are cleared once promoted.",
             check_append_only_files(files)),
            ("A new Agent Log entry is over the cap the log sets for itself",
             "The log caps Section 1 entries at 120 words. Trim the new entry; the "
             "old ones stay as written.",
             check_new_log_entries_length(files)),
            ("There is an instruction file that should not be here",
             "Agents load these as rules automatically, wherever they sit, without "
             "telling you. Only CLAUDE.md and AGENTS.md at the top of the vault are "
             "meant to exist. If you did not write it, delete it. If you did, move "
             "what it says into Maps & Manuals, where rules belong.",
             check_stray_instruction_files()),
        ]

    total = sum(len(issues) for _, _, issues in checks)
    passed = [name for name, _, issues in checks if not issues]

    for name, fix, issues in checks:
        if not issues:
            continue
        count = len(issues)
        print(f"  {count} {'problem' if count == 1 else 'problems'}: {name.lower()}")
        for line in issues:
            print(f"    {line.strip()}")
        print(f"    -> {fix}\n")

    if passed:
        print(f"  {len(passed)} other check(s) passed.\n")

    warnings = (warn_onboarding_state() + warn_local_permission_grants()
                + warn_stale_questions(files)
                + warn_card_blanks()
                + warn_system_state() + warn_stale_efforts()
                + warn_expired_content(files) + warn_effort_names_in_skills(files)
                + warn_skill_list_budget()
                + warn_entry_file_budget()
                + warn_tags_without_changelog())
    if warnings:
        print("Worth a look, but nothing is blocked:")
        for line in warnings:
            print(f"  {line.strip()}")
        print()

    print("=" * 60)
    if total == 0:
        print("Nothing to fix.")
    else:
        thing = "thing" if total == 1 else "things"
        print(f"{total} {thing} to fix. Saving is blocked until they are.")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
