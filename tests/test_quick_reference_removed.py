from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ME = ROOT / "template" / "Maps & Manuals" / "Me.md"


class QuickReferenceRemovedTests(unittest.TestCase):
    def test_quick_reference_no_longer_restates_the_cards_where_to_go_table(self):
        """The 'Quick reference' block sat below <!-- END CARD --> (so it never
        reached an agent automatically) yet restated, in prose, routing already
        in the CARD's 'Where to go' table: Active Context, Vault Map, Skill Map,
        and Writing Style. Its 'Default task flow' step 1 also told an agent to
        unconditionally read Active Context every task, contradicting Agent
        Rules.md's narrower 'do not load it for an unrelated self-contained
        question'. Flagged in T05.3 for T05.4 to resolve.
        """
        text = ME.read_text(encoding="utf-8")
        self.assertNotIn("## Quick reference", text)
        self.assertNotIn("Default task flow", text)
        self.assertNotIn("Task routing:", text)
        self.assertNotIn("Available workflows:", text)


if __name__ == "__main__":
    unittest.main()
