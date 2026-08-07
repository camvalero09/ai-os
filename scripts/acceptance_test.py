#!/usr/bin/env python3
"""Prove a vault is usable by an agent that has never seen it.

The lint checker answers "is this vault internally consistent". This answers a
different question: "would a cold agent, given only these files, find its way".
Those come apart. Every link can resolve while the entry point points at a file
that says nothing useful, and nothing would notice.

Run it after installing, after updating, and after any change to the reading
path or the folder layout:

    python3 System/scripts/acceptance_test.py

What it cannot check is the last step, whether an agent actually behaves
correctly. That needs a real agent in a fresh session and is described at the
bottom of the output. This script gets everything mechanical out of the way so
that human step is short.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_paths as _paths

VAULT, SYSTEM = _paths.VAULT, _paths.SYSTEM

results: list[tuple[bool, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((ok, name, detail))


def read(rel: str) -> str:
    p = VAULT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main() -> int:
    # This test asks whether a vault is usable. Run against the bare system
    # repository there is no vault to judge, and reporting a dozen failures
    # would read as breakage rather than as the wrong folder.
    if not ((VAULT / "Maps & Manuals").is_dir() and (VAULT / "Ideaverse").is_dir()):
        print("Acceptance test")
        print("=" * 60)
        print(f"  {VAULT} is the system on its own, not somebody's vault.")
        print("  There is nothing here to judge: no entry point, no notes, no owner.\n")
        print("  Run this from inside an installed vault, the folder that holds System/.")
        return 0

    # 1. The entry point exists and redirects rather than holding rules itself.
    entry = read("CLAUDE.md")
    check("CLAUDE.md exists", bool(entry))
    check("CLAUDE.md names Me.md as the first read", "Me.md" in entry or "Me|" in entry)
    check("CLAUDE.md names Active Context", "Active Context" in entry)
    # Same normalization the linter uses: neutralize both names in both files,
    # so each may refer to itself and to the other without counting as drift.
    def neutral(text: str) -> str:
        return text.replace("CLAUDE.md", "ENTRY").replace("AGENTS.md", "ENTRY")
    check("AGENTS.md matches CLAUDE.md",
          neutral(read("AGENTS.md")) == neutral(entry),
          "the two entry points must stay identical")

    # 2. The files it sends an agent to are real and not empty scaffolding.
    for rel, floor in (("Maps & Manuals/Me.md", 40),
                       ("Maps & Manuals/Active Context.md", 10),
                       ("Maps & Manuals/Vault Map.md", 20),
                       ("Maps & Manuals/Skill Map.md", 20)):
        body = read(rel)
        check(f"{rel} is present and substantive",
              len(body.splitlines()) >= floor,
              f"{len(body.splitlines())} lines, expected at least {floor}")

    # 3. Routing: a task named in Active Context must reach a file that exists.
    ctx = read("Maps & Manuals/Active Context.md")
    targets = re.findall(r"\[\[([^\]|\\]+)", ctx)
    broken = [t for t in targets if not (VAULT / f"{t.strip()}.md").exists()]
    check("every routing link in Active Context resolves",
          not broken, "; ".join(broken[:3]))

    # 4. The skills an agent is told about are actually installed.
    skill_map = read("Maps & Manuals/Skill Map.md")
    listed = set(re.findall(r"\[\[(System/Skills/[^\]|\\]+)", skill_map))
    missing = [s for s in listed if not (VAULT / f"{s}.md").exists()]
    check(f"all {len(listed)} skills in the Skill Map exist", not missing, "; ".join(missing[:3]))

    # 5. The agent loaders match the skills that asked to be exposed.
    exposed = {p for p in (SYSTEM / "Skills").rglob("*.md")
               if "expose: claude_code" in p.read_text(encoding="utf-8")}
    loaders = list((VAULT / ".claude/skills").glob("*/SKILL.md"))
    check(f"{len(exposed)} exposed skills have {len(loaders)} loaders",
          len(loaders) >= len(exposed),
          "run build_views.py if these disagree")

    # 6. The boundary that the whole split rests on.
    check("System/ is present", (VAULT / "System").is_dir())
    check("System/ is ignored by the vault's git",
          "System/" in read(".gitignore"),
          "otherwise the vault tries to track a second copy of the system")
    check("the vault marker exists", (VAULT / ".aios-vault").exists(),
          "without it the scripts cannot find the vault root")

    # 7. Secrets are not about to be committed.
    gi = read(".gitignore")
    for pattern in ("credentials/", "*.json.key", "vault.config.json"):
        check(f"gitignore covers {pattern}", pattern in gi)

    # 8. A per-vault identity exists, since tools refuse to guess one.
    cfg = VAULT / "vault.config.json"
    if cfg.exists():
        try:
            keys = set(json.loads(cfg.read_text()))
        except ValueError:
            keys = set()
        check("vault.config.json is valid JSON with an owner", "owner_name" in keys,
              "onboarding fills this in")
    else:
        check("vault.config.json exists", False, "copy vault.config.example.json and fill it in")

    passed = sum(1 for ok, _, _ in results if ok)
    print("Acceptance test")
    print("=" * 60)
    for ok, name, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok and detail:
            print(f"        {detail}")
    print("=" * 60)
    print(f"{passed}/{len(results)} passed\n")

    if passed == len(results):
        print("Mechanically sound. One step remains and only a person can do it:\n")
        print("  Open a NEW agent session in this vault with no other context and ask")
        print("  something vague and real, for example:")
        print('    "I want to start tracking my apartment search. Set it up."\n')
        print("  It passes if the agent reads Me.md and Active Context before acting,")
        print("  creates a properly structured note with frontmatter, refuses to")
        print("  hand-edit a generated table, and warns that the commit check will")
        print("  block until the tables are rebuilt. It fails if it starts writing")
        print("  files without reading anything first.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
