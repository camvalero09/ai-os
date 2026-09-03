from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "Agent Rules.md"
ME = ROOT / "template" / "Maps & Manuals" / "Me.md"
WORKING_FROM_A_CLONE = ROOT / "Skills" / "Tools" / "Working From a Clone.md"


class PushPermissionContractTests(unittest.TestCase):
    def test_agent_rules_states_the_one_position(self):
        text = RULES.read_text(encoding="utf-8")
        self.assertIn("Push only when explicitly asked", text)

    def test_me_clone_section_does_not_instruct_an_unconditional_push(self):
        """The 'if you are not running on the owner's laptop' section told an
        agent to 'push, or say clearly that you did not' at every session
        close, with no mention of asking first. That reads as an unconditional
        push instruction and contradicts Agent Rules.md's 'push only when
        explicitly asked'.
        """
        text = ME.read_text(encoding="utf-8")
        self.assertNotIn("and push, or say clearly that you did not", text)
        clone_section = text.split("## If you are not running on the owner's laptop", 1)[1]
        clone_section = clone_section.split("\n## ", 1)[0]
        self.assertIn("push only when", clone_section.lower())

    def test_working_from_a_clone_skill_does_not_instruct_an_unconditional_push(self):
        text = WORKING_FROM_A_CLONE.read_text(encoding="utf-8")
        self.assertNotIn("and push, or say clearly that you did not", text)
        self.assertIn("push only when", text.lower())


if __name__ == "__main__":
    unittest.main()
