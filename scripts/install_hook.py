#!/usr/bin/env python3
"""Install the vault git hooks. Works on macOS, Linux and Windows.

Two hooks: pre-commit runs the lint, commit-msg requires a Session: line on
agent commits.

Why this exists rather than a one-line `ln -sf`: symlinks do not survive zip or
AirDrop transfer reliably, and on Windows they need developer mode or admin
rights. So instead of linking, this writes a two-line shim into .git/hooks that
calls the real script in scripts/. The shim never changes, so edits to
System/scripts/pre-commit still take effect immediately.

Git for Windows ships bash and runs hooks through it, so one shell shim covers
every platform.

    python3 scripts/install_hook.py        # or `python` on Windows
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

SHIM = """#!/bin/sh
# Installed by install_hook.py. Calls the real hook, which is versioned.
exec "$(git rev-parse --show-toplevel)/{rel}" "$@"
"""


def main() -> int:
    try:
        root = Path(subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        print("Not inside a git repository. Run `git init` first.", file=sys.stderr)
        return 1

    hooks = root / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)

    for name in ("pre-commit", "commit-msg"):
        real = root / "System" / "scripts" / name
        if not real.exists():
            real = root / "scripts" / name  # system repo run on its own
        if not real.exists():
            print(f"Missing {real}. Is this a complete vault?", file=sys.stderr)
            return 1

        target = hooks / name
        if target.is_symlink() or target.exists():
            target.unlink()
        target.write_text(SHIM.format(rel=real.relative_to(root).as_posix()),
                          encoding="utf-8")

        if os.name != "nt":
            # Windows has no execute bit; git-bash runs the hook regardless.
            for f in (target, real):
                f.chmod(f.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        print(f"Hook installed at {target}")
    print("Verify it works by trying to commit a note with an invalid status:")
    print("  a hook that is not installed looks exactly like one that passes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
