#!/usr/bin/env python3
"""Give an older vault the card, so updates to the shared rules reach it.

From v2.26 the entry files are built from two cards: a personal one in
`Maps & Manuals/Me.md` and the shared one in `System/Agent Rules.md`. A vault
installed before that has neither markers nor a generated CLAUDE.md, and
`build_views.py` deliberately does nothing when it finds no card, because
overwriting somebody's hand-written CLAUDE.md is the worst possible way to
deliver an update. So such a vault receives every future improvement to the
rules as nothing at all until this runs once.

    python3 System/scripts/adopt_card.py          # say what would change
    python3 System/scripts/adopt_card.py --yes    # do it

It inserts a small personal card near the top of Me.md and leaves every word
already in that file exactly where it is, below the card. Nothing is deleted
and nothing is guessed: the slots it writes are placeholders for the owner to
fill in, because only they know what belongs there.

Run `python3 System/scripts/build_views.py` afterwards to write CLAUDE.md and
AGENTS.md from the result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent.parent
VAULT_MARKER = ".aios-vault"


def vault_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / VAULT_MARKER).exists():
            return parent
    return None


def scaffold(owner: str, language: str) -> str:
    """The personal half, with the owner's own facts left as blanks.

    Only what is true of this person goes here. Everything general already
    lives in the shared card and arrives with each update, so repeating a rule
    here would mean maintaining it twice and having it drift.
    """
    who = owner or "the owner"
    return f"""<!-- BEGIN CARD -->
## Who {who} is

TO FILL IN. Where they live and where they are from. What they do and what
they know well. Whether they write code, because an agent that assumes wrong
is either impenetrable or condescending. Any word that must be explained in
plain language rather than used as jargon.

## Language and forms of address

{language.capitalize() if language else "TO FILL IN"} by default; another language when the audience or jurisdiction
requires it. TO FILL IN: any standing rule about how a particular person is
addressed.

## Files here that only ever grow

TO FILL IN. Name any log, timeline or decision table in this vault that must
never be regenerated, reordered or rewritten. The shared rules already cover
Agent Log Section 1, weekly reviews and decision tables.

## Where to go

| Task | Go to |
|---|---|
| What is active now | [[Maps & Manuals/Active Context\\|Active Context]] |
| Where a file belongs | [[Maps & Manuals/Vault Map\\|Vault Map]] |
| A workflow or tool not listed at startup | [[Maps & Manuals/Skill Map\\|Skill Map]] |
| Writing anything others will read | [[Maps & Manuals/Writing Style\\|Writing Style]] |
| Find an existing note | [[Ideaverse/Atlas/Atlas Index\\|Atlas Index]] or [[Ideaverse/Efforts/Efforts Index\\|Efforts Index]] |
| A specific person | [[Ideaverse/Atlas/Atlas Index\\|Atlas Index]], then `Atlas/People/` |
| A new source to process | [[System/Skills/Workflows/Process Source into Atlas\\|Process Source into Atlas]] |

TO FILL IN: one row per effort, so an agent routes without searching.
<!-- END CARD -->
"""


def main() -> int:
    vault = vault_root()
    if vault is None:
        print("Not inside a vault: no .aios-vault marker above this script.")
        return 2

    me = vault / "Maps & Manuals/Me.md"
    if not me.exists():
        print(f"No {me.relative_to(vault)} to migrate.")
        return 2

    text = me.read_text(encoding="utf-8")
    if "<!-- BEGIN CARD -->" in text:
        print(f"{me.relative_to(vault)} already has a card. Nothing to do.")
        print("Run: python3 System/scripts/build_views.py")
        return 0

    cfg = vault / "vault.config.json"
    owner = language = ""
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            owner = str(data.get("owner_name") or "").split()[0] if data.get("owner_name") else ""
            language = str(data.get("primary_language") or "")
        except (json.JSONDecodeError, OSError, IndexError):
            pass

    lines = text.splitlines(keepends=True)
    # After the title, so the card is the first thing anyone opening the file
    # sees, and above whatever the vault already had, which is kept verbatim.
    at = 1 if lines and lines[0].startswith("# ") else 0
    block = scaffold(owner, language)
    intro = ("\n**The card below is the only part of this file agents receive "
             "automatically.** It is joined with `System/Agent Rules.md` to build "
             "`CLAUDE.md` and `AGENTS.md`. Edit the card here; run "
             "`python3 System/scripts/build_views.py` to publish.\n\n"
             "Everything below the card is kept for reference and is read only "
             "when an agent opens this file.\n\n")
    new = "".join(lines[:at]) + intro + block + "\n" + "".join(lines[at:])

    if "--yes" not in sys.argv:
        print(f"Would add a personal card to {me.relative_to(vault)}:\n")
        print(f"  {len(block.splitlines())} lines inserted after the title")
        print(f"  {len(lines)} existing lines kept, unchanged, below it")
        print("  nothing deleted, nothing rewritten\n")
        print("The card has blanks marked TO FILL IN that only the owner can answer.")
        print("Re-run with --yes to write it.")
        return 0

    me.write_text(new, encoding="utf-8")
    print(f"Added the card to {me.relative_to(vault)}.")
    print("\nNext, in this order:")
    print("  1. Fill in every TO FILL IN in the card.")
    print("  2. python3 System/scripts/build_views.py")
    print("  3. python3 System/scripts/vault_lint.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
