from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "Agent Rules.md"
SAVING = ROOT / "Skills/Workflows/Saving Work.md"
SESSIONS = ROOT / "Skills/Tools/Sessions.md"

# A command invocation inside the always-loaded rules is procedure, not a rule.
# Procedure belongs in a skill that loads when the work actually happens; the
# rules layer states the obligation and names the skill.
COMMAND_PATTERN = re.compile(r"`[^`]*(?:git |python3 |\.py\b|npm |bash )[^`]*`")


def card() -> str:
    text = RULES.read_text(encoding="utf-8")
    return text.split("<!-- BEGIN CARD -->", 1)[1].split("<!-- END CARD -->", 1)[0]


class RulesCarryNoProcedureTests(unittest.TestCase):
    def test_shared_card_contains_no_command_invocations(self):
        found = COMMAND_PATTERN.findall(card())
        self.assertEqual(
            [], found,
            "the always-loaded rules must not carry runnable commands; move them "
            "into the skill that performs the work",
        )

    def test_checkpoint_obligation_survives_in_the_rules(self):
        text = card()
        self.assertIn("Create a Git checkpoint after a completed substantive unit", text)
        self.assertIn("Stage only explicit new paths changed for that unit", text)
        self.assertIn("never stage the whole vault", text)
        self.assertIn("Push only when explicitly asked", text)
        self.assertIn("Saving Work", text)

    def test_checkpoint_mechanics_moved_into_the_saving_work_skill(self):
        self.assertTrue(SAVING.exists(), "Skills/Workflows/Saving Work.md must exist")
        text = SAVING.read_text(encoding="utf-8")
        self.assertIn("git commit -o -F <message file> -- <paths>", text)
        self.assertIn("it cannot see a file git has never heard of", text)
        self.assertIn("preserve the changes", text)

    def test_coordination_obligation_survives_and_names_the_sessions_skill(self):
        text = card()
        self.assertIn("Before editing, inspect the working tree", text)
        self.assertIn("A missing heartbeat is not proof that the vault is clear", text)
        self.assertIn("Sessions", text)

    def test_sessions_skill_carries_the_command(self):
        self.assertTrue(SESSIONS.exists())
        self.assertIn("sessions.py", SESSIONS.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
