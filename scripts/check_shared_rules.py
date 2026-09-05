#!/usr/bin/env python3
"""Refuse to publish a personal detail inside the shared rules file.

`Agent Rules.md` is the one file whose contents are loaded by every agent in
every installation. It is also the newest way for this system to leak: before
it existed there was no shared prose file to write a name into by accident.

This repository already paid for that mistake once. CHANGELOG.md records why
there is no history before v2.0: the earlier commits "carried the author's own
name, email, home paths and other personal detail", and publishing them would
have made all of it permanent and public. A tag cannot be amended, so the check
has to happen before the commit, not after the release.

    python3 scripts/check_shared_rules.py            # check, print, exit 1 on a hit

Two kinds of pattern. The universal ones need no vault and always run, so the
check works in the system repository where there is no vault to read. The
derived ones are the owner's own name, the people they keep notes on and their
effort names, read from the vault when the script is running inside one.

Exit code 0 means clean, 1 means something personal is in there, 2 means the
file is missing.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYSTEM = HERE.parent
SHARED_RULES = SYSTEM / "Agent Rules.md"

# Always checked, vault or no vault. Each is something that cannot be true of
# every installation, so it has no business in a file every installation loads.
UNIVERSAL = [
    (re.compile(r"/(?:Users|home)/(?!<)[A-Za-z0-9._-]+"), "a home path"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "an email address"),
    (re.compile(r"\b(?:\+\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b"), "a phone number"),
    (re.compile(r"\biban\b|\bswift\b|\bbic\b", re.I), "a bank identifier"),
]

# Words that look like a name to the derived check but are part of the system's
# own vocabulary. Without this, an effort called "Trip Planning" would make the
# phrase "trip planning" unwritable in shared prose.
STOPWORDS = {"me", "system", "vault", "inbox", "atlas", "efforts", "archive",
             "sources", "outputs", "calendar", "people"}


def vault_root() -> Path | None:
    for parent in [HERE] + list(HERE.parents):
        if (parent / ".aios-vault").exists():
            return parent
    return None


def git_identity_terms() -> list[tuple[str, str]]:
    """Whoever is committing, read from git.

    The system repository has no vault to read, and it is precisely where the
    commit that would publish a leak gets made. The author's own name is the
    detail the pre-v2.0 history leaked, so it is the one worth catching even
    when nothing else about the owner is knowable here.
    """
    terms: list[tuple[str, str]] = []
    for key, label in (("user.name", "the name git is committing under"),
                       ("user.email", "the address git is committing under")):
        try:
            r = subprocess.run(["git", "-C", str(SYSTEM), "config", "--get", key],
                               capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode != 0:
            continue
        for word in r.stdout.split("@")[0].replace(".", " ").split():
            if len(word) > 3 and word.lower() not in STOPWORDS:
                terms.append((word, label))
    return terms


def derived_terms(vault: Path) -> list[tuple[str, str]]:
    """The owner's name, the people they track, and their effort names."""
    terms: list[tuple[str, str]] = []

    cfg = vault / "vault.config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        for key in ("owner_name", "vault_name", "google_account"):
            value = str(data.get(key) or "").strip()
            # An address contributes its local part only. Blocking the provider
            # would make "gmail" unwritable in shared prose, which is a false
            # positive on a check that refuses commits.
            value = value.split("@")[0]
            for word in value.replace(".", " ").replace("_", " ").split():
                if len(word) > 3 and word.lower() not in STOPWORDS:
                    terms.append((word, f"the owner's {key.replace('_', ' ')}"))

    people = vault / "Ideaverse/Atlas/People"
    if people.is_dir():
        for note in people.glob("*.md"):
            if note.stem.lower() in STOPWORDS:
                continue
            for word in note.stem.split():
                if len(word) > 3 and word.lower() not in STOPWORDS:
                    terms.append((word, "a person this vault keeps a note on"))

    efforts = vault / "Ideaverse/Efforts"
    if efforts.is_dir():
        for folder in efforts.iterdir():
            if folder.is_dir() and folder.stem.lower() not in STOPWORDS:
                terms.append((folder.stem, "an effort name"))

    # Longest first, so a full effort name is reported instead of one word of it.
    return sorted(set(terms), key=lambda t: -len(t[0]))


SHIPPED_DIRS = ("Skills", "scripts", "template")
AUTHORING_ONLY = {
    "CHANGELOG.md", "IMPLEMENTATION_PLAN.md", "MAINTAINER_RULES.md",
    "T03_RULES_PROPOSAL.md", "AGENTS.md", "CLAUDE.md", "README.md",
    "SETUP.md", "SETUP-WINDOWS.md",
}
SHIPPED_SUFFIXES = {".md", ".py", ".json", ".sh", ""}


def shipped_files() -> list[Path]:
    """Every file an adopter receives, and none that only a maintainer reads.

    SETUP guides and the README are excluded because they legitimately carry
    the repository URL and its owner's account name; tests and evaluation
    fixtures never reach a vault.
    """
    root = SHARED_RULES.parent
    files = [SHARED_RULES] if SHARED_RULES.exists() else []
    for name in SHIPPED_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix not in SHIPPED_SUFFIXES:
                continue
            if path.name in AUTHORING_ONLY:
                continue
            files.append(path)
    return files


def check_all() -> list[tuple[Path, str]]:
    """Personal detail in anything that ships, as (file, problem) pairs."""
    found = []
    for path in shipped_files():
        for problem in check(path):
            found.append((path, problem))
    return found


PLACEHOLDER = re.compile(
    r"example[.-]|@example|\byour[-.]|\bplaceholder\b|1234567890|\bxxx+\b", re.I)


def check(path: Path = SHARED_RULES) -> list[str]:
    """Every reason this file must not be published, one per line."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    # The preamble above the card explains the rule and has to be able to say
    # the words it forbids. Only the card itself ships to other vaults.
    card = re.search(r"<!-- BEGIN CARD -->\n(.*?)<!-- END CARD -->", text, re.DOTALL)
    body = card.group(1) if card else text

    problems = []
    seen = set()
    for pattern, label in UNIVERSAL:
        for m in pattern.finditer(body):
            hit = m.group(0)
            if hit.lower() in seen or PLACEHOLDER.search(hit):
                continue
            seen.add(hit.lower())
            problems.append(f'"{hit}" looks like {label}')

    vault = vault_root()
    named = (derived_terms(vault) if vault else []) + git_identity_terms()
    for term, label in named:
        if term.lower() in seen:
            continue
        if re.search(rf"\b{re.escape(term)}\b", body, re.I):
            seen.add(term.lower())
            problems.append(f'"{term}" is {label}')
    return problems


def main() -> int:
    if not SHARED_RULES.exists():
        print(f"No shared rules file at {SHARED_RULES}.")
        return 2
    problems = check_all()
    scanned = len(shipped_files())
    if not problems:
        print(f"Shared files: clean, nothing personal in {scanned} files that ship.")
        return 0
    root = SHARED_RULES.parent
    print("Files that ship to every installation contain personal detail:\n")
    for path, problem in problems:
        print(f"  {path.relative_to(root)}: {problem}")
    print("\nEvery installation loads these and a published version cannot be")
    print("amended. Move the detail into the owner's own card in Maps & Manuals/Me.md.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
