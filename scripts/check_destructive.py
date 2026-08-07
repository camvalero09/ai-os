#!/usr/bin/env python3
"""Pre-command safety check for an AI OS vault.

Runs as a Claude Code PreToolUse hook on every Bash command. If the command
matches a destructive pattern, it returns "ask" so the user confirms before it
runs. It never blocks outright: every warning can be approved.

The rules it enforces already exist as prose in Maps & Manuals/Me.md. Prose
rules depend on an agent remembering them. This one does not.

Wired up in .claude/settings.json. To disable, remove the hooks block there.
"""

import json
import re
import sys

# (compiled pattern, what to tell the user)
RULES = [
    (r"\bgit\s+add\s+(-A\b|--all\b|\.(\s|$))",
     "Stages every change in the vault, including work another session may have "
     "in progress. Me.md says to stage only the explicit paths you edited."),

    (r"\bgit\s+reset\s+--hard\b",
     "Throws away uncommitted work permanently. There is no undo."),

    (r"\bgit\s+clean\s+-[a-z]*f",
     "Deletes untracked files permanently. Anything not yet committed is gone."),

    (r"\bgit\s+(push\s+.*(--force|-f)\b|push\s+--force)",
     "Rewrites history on the remote. Any other clone of this repo breaks."),

    (r"\bgit\s+(checkout|restore)\s+\.(\s|$)",
     "Discards all uncommitted changes in the working tree."),

    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*\s|-[a-zA-Z]*f[a-zA-Z]*\s)",
     "Recursive or forced delete. Me.md says archive beats deleting, and never "
     "delete raw sources."),

    (r"\bgit\s+filter-repo\b",
     "Rewrites the entire history. Every commit identifier changes and other "
     "clones become incompatible."),

    (r"\bgit\s+branch\s+-D\b",
     "Force-deletes a branch even if its commits are not merged anywhere."),
]

# Deleting these is routine and safe: they are rebuildable caches, not content.
SAFE_TARGETS = re.compile(
    r"(__pycache__|\.pyc\b|node_modules|\.DS_Store|/tmp/|\.pytest_cache|\.ruff_cache)"
)


def check(command: str):
    """Return a reason string if the command should be confirmed, else None."""
    for pattern, reason in RULES:
        if re.search(pattern, command):
            if pattern.startswith(r"\brm") and SAFE_TARGETS.search(command):
                continue  # rebuildable cache, not vault content
            return reason
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never break the session over a malformed payload

    if payload.get("tool_name") != "Bash":
        return 0

    command = (payload.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0

    reason = check(command)
    if reason is None:
        return 0

    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"Destructive command check: {reason}",
        }
    }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
