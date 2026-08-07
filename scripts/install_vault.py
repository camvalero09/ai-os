#!/usr/bin/env python3
"""Turn an empty folder into a working vault.

Run it from the folder you want the vault to live in, once the system is
cloned inside it:

    mkdir ~/Documents/MyVault && cd ~/Documents/MyVault
    git clone https://github.com/camvalero09/ai-os.git System
    python3 System/scripts/install_vault.py

It seeds the vault from the system's `template/`, wires the agent settings and
the commit check, generates the index tables, and runs the checker. It refuses
to touch a folder that already has notes in it unless you pass --force, because
overwriting somebody's Me.md is not recoverable from here.

Everything it creates belongs to this vault alone. The system stays in System/,
is never edited here, and is updated by version tag.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent.parent
VAULT = Path.cwd()

# Present in a vault that has already been set up. Seeding over these would
# destroy the owner's own writing, so their presence stops the install.
OWNED = ["Maps & Manuals/Me.md", "Maps & Manuals/Active Context.md", "Ideaverse", "CLAUDE.md"]


def run(*args, cwd=None) -> tuple[int, str]:
    r = subprocess.run(args, cwd=cwd or VAULT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    force = "--force" in sys.argv

    if SYSTEM.parent != VAULT:
        print(f"Run this from the folder that contains System/, not from {VAULT}.")
        print(f"The system is installed at {SYSTEM}, so run it from {SYSTEM.parent}.")
        return 1

    template = SYSTEM / "template"
    if not template.is_dir():
        print(f"No template/ inside {SYSTEM}. Is the system clone complete?")
        return 1

    existing = [p for p in OWNED if (VAULT / p).exists()]
    if existing and not force:
        print("This folder already looks like a vault:")
        for p in existing:
            print(f"  {p}")
        print("\nNothing was changed. Pass --force only if you mean to overwrite these.")
        return 1

    print(f"Installing a vault in {VAULT}\n")

    # 1. Seed the vault's own files from the template.
    copied = 0
    for src in sorted(template.rglob("*")):
        rel = src.relative_to(template)
        dst = VAULT / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    print(f"  seeded {copied} file(s) from the system template")

    # 2. Agent settings. The canonical copy lives in the system and is replaced
    #    on every update, so it is copied rather than edited here.
    (VAULT / ".claude").mkdir(exist_ok=True)
    shutil.copy2(SYSTEM / "claude-settings.json", VAULT / ".claude/settings.json")
    print("  wrote .claude/settings.json")

    # 3. Folders that hold things git must never see.
    for d in ("credentials", "logs"):
        (VAULT / d).mkdir(exist_ok=True)
    print("  created credentials/ and logs/, both gitignored")

    # 4. Folders the Vault Map documents and the routing table sends people to.
    #    Without these the map describes a shape the vault does not have, and
    #    following it fails on the first try.
    placeholders = {
        "Ideaverse/Archive/README.md":
            "# Archive\n\nFinished or inactive material. Efforts with no movement in 60 days "
            "move here, keeping their folder. Nothing is deleted; archiving beats deleting.\n",
        "Skills/Workflows/README.md":
            "# Your own workflows\n\nRepeatable processes that belong to you alone and are never "
            "shared with anyone else's vault.\n\nShared workflows live in `System/Skills/Workflows/` "
            "and arrive with each update. If something you write here would help anyone, it can be "
            "proposed upstream: see [[System/Skills/Tools/Update System|Update System]].\n",
        "Skills/Tools/README.md":
            "# Your own tools\n\nNotes on tools and integrations specific to you: an employer's "
            "systems, a client's stack, a property you manage.\n\nAnything naming an employer, client "
            "or family member belongs here rather than in the shared system.\n",
    }
    made = 0
    for rel, body in placeholders.items():
        dst = VAULT / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(body, encoding="utf-8")
        made += 1
    if made:
        print(f"  created {made} folder(s) the Vault Map refers to")

    # 4. Per-vault identity, only if it is not already there.
    cfg, example = VAULT / "vault.config.json", VAULT / "vault.config.example.json"
    if not cfg.exists() and example.exists():
        shutil.copy2(example, cfg)
        print("  created vault.config.json from the example, fill it in next")

    # 5. Git, then the commit check.
    if not (VAULT / ".git").exists():
        code, out = run("git", "init")
        print("  git init" if code == 0 else f"  git init failed: {out}")
    code, out = run(sys.executable, str(SYSTEM / "scripts/install_hook.py"))
    print("  installed the commit check" if code == 0 else f"  hook install failed: {out}")

    # 6. Generated tables and loaders, then prove the result is consistent.
    code, out = run(sys.executable, str(SYSTEM / "scripts/build_views.py"))
    print("  generated the index tables and agent loaders" if code == 0 else f"  build failed: {out}")

    code, out = run(sys.executable, str(SYSTEM / "scripts/vault_lint.py"))
    print("\n" + ("  the vault checks out clean" if code == 0 else "  the checker reported problems:\n" + out))

    # A first save, so there is always something to go back to. The very first
    # mistake is the one most likely to happen and the one with nothing behind
    # it. Skipped only if the vault already has history.
    has_history = run("git", "rev-parse", "HEAD")[0] == 0
    if not has_history:
        run("git", "add", "-A")
        c, msg = run("git", "-c", "user.name=AI OS", "-c", "user.email=noreply@localhost",
                     "commit", "--no-verify", "-m",
                     "First save: a fresh vault, before anything personal is in it")
        print("  made a first save to roll back to" if c == 0
              else f"  could not make the first save: {(msg.splitlines() or ['unknown'])[0]}")

    # A clone made without tags cannot name its version, and git says so in a
    # sentence that reads like a crash on somebody's first evening. Nothing here
    # depends on the answer, so an unknown version is a blank, not an error.
    rc, version = run("git", "describe", "--tags", cwd=SYSTEM)
    print(f"\nDone. System version {version}.\n" if rc == 0 and version
          else "\nDone.\n")
    print("Next, in this order:")
    print("  1. Fill in vault.config.json: your name, timezone, language.")
    print("  2. Open the folder in Obsidian, and in Claude Code accept the trust prompt once.")
    print("  3. Say /onboard to your agent and answer its questions.")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
