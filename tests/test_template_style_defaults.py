from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ME = ROOT / "template" / "Maps & Manuals" / "Me.md"


def full_text() -> str:
    return ME.read_text(encoding="utf-8")


class TemplateStyleDefaultTests(unittest.TestCase):
    def test_shipped_card_does_not_duplicate_rigid_rules_agent_rules_replaced(self):
        text = full_text()

        # Formatting rules Agent Rules.md deliberately made adaptive
        # ("Match the length, structure, and tone... not by formula").
        self.assertNotIn("Three sentences per paragraph", text)
        self.assertNotIn("A header or list every two paragraphs", text)
        self.assertNotIn("Bullets carry a bold lead-in", text)

        # Voice/punctuation preferences Agent Rules.md assigns to the owner's
        # own files (Writing Style.md), not a shipped shared default.
        self.assertNotIn("No buzzwords, no em dashes", text)
        self.assertNotIn("Using em dashes", text)

        # Evidence and hedging rules restated from the shared card.
        self.assertNotIn("Do not claim to have read a file without reading it", text)
        self.assertNotIn("Do not invent facts", text)
        self.assertNotIn(
            "Saying \"it depends\" without explaining what it depends on", text
        )
        self.assertNotIn("Padding with encouragement or affirmations not asked for", text)
        self.assertNotIn(
            "without first reading the complete source", text
        )

        # The stale single-source-of-truth claim this file made before
        # Agent Rules.md became the shared half.
        self.assertNotIn("This is the single source of truth", text)


if __name__ == "__main__":
    unittest.main()
