#!/usr/bin/env python3
"""Compare this laptop's record of what happened against the copy on GitHub.

The other protections try to prevent a history being rewritten. This one
assumes prevention failed and asks a different question: has it happened.

That matters because prevention is not achievable here. Every local guard
sits on the same machine as the thing it guards, and an agent with a shell
can go around any of it. What is achievable is that nothing can be changed
quietly, and this is the check that makes it loud.

It compares commit history rather than file contents, on purpose. A working
copy always differs from the remote between saves, so comparing contents
would report a problem every single week and be ignored by the third one.

    python3 System/scripts/check_history_remote.py

Run during weekly maintenance. Reports and exits 0 unless something is
actually wrong, in which case it exits 1 and says what to look at.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_paths as _paths

VAULT = _paths.VAULT


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(VAULT), *args],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def bare(line: str) -> str:
    """Ignore link targets: a moved file's links must be repointed to work."""
    return re.sub(r"\[\[[^\]]*\]\]", "[[]]", line)


def main() -> int:
    protected = [p for p in git("ls-files").splitlines()
                 if p.endswith("Project_log.md") or p.endswith("Agent Log.md")]
    if not protected:
        print("No history files yet, so nothing to compare.")
        return 0

    if not git("remote"):
        print("This vault has no remote, so there is no second copy to compare against.")
        print("That is the whole protection: a record kept only on this laptop can be")
        print("changed on this laptop with nothing left to notice.")
        return 0

    # Fetch rather than pull: this reads the remote, it never changes the vault.
    subprocess.run(["git", "-C", str(VAULT), "fetch", "--quiet"],
                   capture_output=True, text=True)
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "main"
    remote_ref = f"origin/{branch}"
    if not git("rev-parse", "--verify", remote_ref):
        print(f"No {remote_ref} on the remote yet. Push once and this starts working.")
        return 0

    problems = []
    for path in protected:
        theirs = git("show", f"{remote_ref}:{path}")
        if not theirs:
            continue  # a file that exists here and not there is new, not altered
        mine = (VAULT / path).read_text(encoding="utf-8") if (VAULT / path).exists() else ""
        if not mine:
            problems.append((path, ["the whole file is gone from this laptop"]))
            continue
        here = {bare(ln) for ln in mine.splitlines()}
        lost = [ln for ln in theirs.splitlines() if ln.strip() and bare(ln) not in here]
        if lost:
            problems.append((path, lost))

    unpushed = git("log", "--oneline", f"{remote_ref}..HEAD")
    n_unpushed = len(unpushed.splitlines()) if unpushed else 0

    print("History, this laptop against GitHub")
    print("=" * 60)
    if not problems:
        print(f"  {len(protected)} record(s) match the copy on GitHub.")
        if n_unpushed:
            print(f"  {n_unpushed} save(s) not yet pushed, which is normal.")
        return 0

    print("  Something on this laptop no longer matches the copy on GitHub.\n")
    for path, lost in problems:
        print(f"  {path}: {len(lost)} line(s) present on GitHub and missing here")
        for line in lost[:3]:
            print(f"      {line[:110]}")
    print("\n  These files only ever grow, so this should not be possible.")
    print("  GitHub holds the true version. To see what changed:")
    print(f"    git diff {remote_ref} -- <the file above>")
    print("  Restore it with: git checkout {} -- <the file above>".format(remote_ref))
    return 1


if __name__ == "__main__":
    sys.exit(main())
