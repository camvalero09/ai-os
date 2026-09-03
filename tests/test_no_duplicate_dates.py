from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITING_STYLE = ROOT / "template" / "Maps & Manuals" / "Writing Style.md"


class NoDuplicateDatesTests(unittest.TestCase):
    def test_writing_style_has_a_single_last_updated_signal(self):
        """Writing Style.md is a Maps & Manuals file like Me.md, Active Context.md
        and Vault Map.md, none of which carry YAML frontmatter. It shipped with
        both a frontmatter `updated:` date and a body 'Last updated:' line, two
        answers to the same question that nothing keeps in sync: the frontmatter
        tracked the last template edit while the body tracked onboarding
        completion, so they could read differently forever.
        """
        text = WRITING_STYLE.read_text(encoding="utf-8")
        self.assertFalse(text.startswith("---\n"), "frontmatter should be removed")
        self.assertIn("Last updated:", text)


if __name__ == "__main__":
    unittest.main()
