#!/usr/bin/env python3
"""Where the system ends and one person's vault begins.

Every script here lives in the shared system, which is installed into a vault at
`System/` and replaced wholesale on update. Nothing personal may resolve relative
to these scripts: credentials and per-vault settings belong to the vault, not to
the system, and a token sitting inside a folder that gets checked out to another
version is both a boundary violation and a way to lose it.

So: the system finds itself from `__file__`, and finds the vault by marker.
"""

from __future__ import annotations

import os
from pathlib import Path

# The system repository root. This file lives in it, so this is never a guess.
SYSTEM = Path(__file__).resolve().parent.parent

VAULT_MARKER = ".aios-vault"


def find_vault_root() -> Path:
    """The folder holding this installation's own notes and secrets.

    An explicit VAULT_ROOT wins. Otherwise walk up from this file looking for
    the marker every content vault carries. Otherwise the system repository is
    being run on its own and is treated as its own vault, which is what makes
    the repo testable without an installation around it.
    """
    override = os.environ.get("VAULT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    for candidate in Path(__file__).resolve().parents:
        if (candidate / VAULT_MARKER).exists():
            return candidate
    return SYSTEM


VAULT = find_vault_root()

# Per-vault secrets. Gitignored, never inside System/, never shared.
CREDENTIALS_DIR = VAULT / "credentials"


def credential(name: str) -> Path:
    """Path to one per-vault secret file.

    Falls back to the pre-split location beside the scripts so an installation
    that has not moved its credentials yet keeps working instead of silently
    failing to authenticate.
    """
    current = CREDENTIALS_DIR / name
    if current.exists():
        return current
    legacy = SYSTEM / "scripts" / name
    if legacy.exists():
        return legacy
    return current


def vault_config() -> dict:
    """Per-vault settings from vault.config.json at the vault root.

    This file is what makes the vault belong to one person. It is created during
    onboarding and is never shared between vaults.
    """
    import json

    path = VAULT / "vault.config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
