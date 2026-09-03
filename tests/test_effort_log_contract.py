from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ME = ROOT / "template" / "Maps & Manuals" / "Me.md"
START_NEW_EFFORT = ROOT / "Skills" / "Workflows" / "Start New Effort.md"
EFFORT_TEMPLATE = ROOT / "Skills" / "Templates" / "Effort.md"


class EffortLogContractTests(unittest.TestCase):
    def test_start_new_effort_names_project_log_as_an_optional_additional_file(self):
        """`Project_log.md` is still mechanically protected as append-only by
        vault_lint.py's check_append_only_files, but no current workflow ever
        creates one. The optional-file list is where an agent learns it exists
        at all, the same way it already learns about Plan.md and Decisions.md.
        """
        text = START_NEW_EFFORT.read_text(encoding="utf-8")
        self.assertIn("Project_log.md", text)

    def test_me_does_not_imply_every_effort_already_has_a_companion_log(self):
        """Me.md's avoid-list used to describe `Project_log.md` as if every
        project folder already carries one beside its note. Start New Effort
        never creates that file for a normal effort, so the claim was stale.
        The bullet must point to where the file actually comes from and must
        not contradict Agent Rules.md's 'Effort notes are not append-only'.
        """
        text = ME.read_text(encoding="utf-8")
        self.assertIn("Start New Effort", text)
        avoid_bullet = [
            line for line in text.splitlines()
            if "Project_log.md" in line and "Rewriting anything that only grows" in line
        ]
        self.assertTrue(avoid_bullet, "expected the avoid-list bullet to mention Project_log.md")
        self.assertIn("when it has one", avoid_bullet[0])


if __name__ == "__main__":
    unittest.main()
