#!/usr/bin/env python3
"""Are this vault's passwords actually being kept out of its backup?

A vault seeded before the secret-patterns fix shipped with no `.gitignore` at
all, so the first save would have committed its own credentials. Anyone who
installed in that window has real Google tokens in a folder that may be
tracked, and nothing tells them.

    python3 System/scripts/check_credentials.py

Four questions, worst first, each with the command that fixes it:

  1. Is a credential tracked by git right now?
  2. Was one ever committed, even if it has since been removed? Git history is
     permanent, so a token in an old commit is still a live token.
  3. Does `.gitignore` cover every pattern a credential lands in?
  4. Is a credential file readable by other accounts on this machine?

It only reads. Nothing here revokes, deletes or commits anything, because the
one irreversible step in a leak, reissuing the token, has to be the owner's.

Exit 0 clean, 1 if something needs doing.
"""

from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent.parent
VAULT_MARKER = ".aios-vault"

# Every credential this system writes lands in one of these.
PATTERNS = ["credentials/", "credentials.json", "*.json.key", ".env", ".env.*"]

# Matched against a path git reports, to decide whether it is a secret.
def is_secret(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (path.startswith("credentials/") or "/credentials/" in path
            or name == "credentials.json" or name.endswith(".json.key")
            or name == ".env" or name.startswith(".env."))


def vault_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / VAULT_MARKER).exists():
            return parent
    return None


def git(vault: Path, *args) -> str:
    try:
        r = subprocess.run(["git", "-C", str(vault), *args],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def check(vault: Path) -> list[str]:
    problems: list[str] = []

    if not (vault / ".git").exists():
        return problems

    tracked = [p for p in git(vault, "ls-files").splitlines() if is_secret(p)]
    if tracked:
        problems.append(
            "A credential is tracked by git right now, so the next save publishes it:")
        problems += [f"    {p}" for p in sorted(tracked)]
        problems.append(
            "    Fix: git rm --cached <file>, confirm .gitignore covers it, save again,")
        problems.append(
            "    then reissue the credential. Assume the old one is compromised.")

    # A file removed from tracking is still in every old commit.
    ever = {p for p in git(vault, "log", "--all", "--pretty=format:",
                           "--name-only", "--diff-filter=A").splitlines()
            if p and is_secret(p)}
    historic = sorted(ever - set(tracked))
    if historic:
        problems.append(
            "A credential was committed in the past. Git history is permanent, so it")
        problems.append("is still readable in an old commit:")
        problems += [f"    {p}" for p in historic]
        problems.append(
            "    Fix: reissue every credential listed. Resetting a token is free and")
        problems.append(
            "    instant, and it is the only thing that makes the old copy worthless.")

    gitignore = vault / ".gitignore"
    if not gitignore.exists():
        problems.append(
            "There is no .gitignore, so nothing is stopping a credential from being")
        problems.append("committed. Fix: copy System/template/.gitignore into the vault.")
    else:
        body = gitignore.read_text(encoding="utf-8")
        missing = [pat for pat in PATTERNS if pat not in body]
        if missing:
            problems.append(
                ".gitignore does not cover every pattern a credential lands in.")
            problems.append(f"    Missing: {', '.join(missing)}")
            problems.append("    Fix: add those lines to .gitignore.")

    creds = vault / "credentials"
    if creds.is_dir():
        loose = [f for f in sorted(creds.iterdir())
                 if f.is_file() and (f.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO))]
        if loose:
            problems.append(
                "A credential file can be read by other accounts on this machine:")
            problems += [f"    {f.name}" for f in loose]
            problems.append(f"    Fix: chmod 600 {creds}/*")

    return problems


def main() -> int:
    vault = vault_root()
    if vault is None:
        print("Not inside a vault: no .aios-vault marker above this script.")
        return 0
    problems = check(vault)
    if not problems:
        print("Credentials: nothing is tracked, nothing is in the history, "
              ".gitignore covers every pattern.")
        return 0
    print("Credentials need attention:\n")
    for line in problems:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
