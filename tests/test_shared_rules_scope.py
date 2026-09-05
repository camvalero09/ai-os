"""The impersonality check must cover every file that ships, not one.

check_shared_rules.py inspected only Agent Rules.md. It reported "clean,
nothing personal in the shared card" on every run of a branch that shipped
the owner's first name in seven skills and scripts, including the sentence
"push only when Camilo has asked for it" in a workflow every adopter loads.

MAINTAINER_RULES.md forbids personal names in shared files, plural. The
checker enforced it for one.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "check_shared_rules.py"


def load():
    spec = importlib.util.spec_from_file_location("shared_rules_scope_test", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SharedFileScopeTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()

    def test_shipped_files_are_enumerated(self):
        self.assertTrue(
            hasattr(self.mod, "shipped_files"),
            "the checker needs to know every file an adopter receives",
        )
        files = {p.relative_to(ROOT).as_posix() for p in self.mod.shipped_files()}
        for expected in ("Agent Rules.md",
                         "Skills/Workflows/Session Handover.md",
                         "Skills/Tools/Working From a Clone.md",
                         "scripts/sessions.py"):
            self.assertIn(expected, files)

    def test_authoring_only_records_are_not_scanned(self):
        files = {p.relative_to(ROOT).as_posix() for p in self.mod.shipped_files()}
        for excluded in ("CHANGELOG.md", "IMPLEMENTATION_PLAN.md",
                         "MAINTAINER_RULES.md", "T03_RULES_PROPOSAL.md"):
            self.assertNotIn(excluded, files,
                             "authoring records may discuss the owner by name")
        self.assertFalse([f for f in files if f.startswith("tests/")])
        self.assertFalse([f for f in files if f.startswith("evaluations/")])

    def test_a_personal_name_in_any_shipped_file_is_reported(self):
        planted = ROOT / "Skills/Workflows/Session Handover.md"
        original = planted.read_text(encoding="utf-8")
        try:
            planted.write_text(
                original + "\nPush only when Camilo has asked for it.\n",
                encoding="utf-8")
            problems = self.mod.check_all()
            self.assertTrue(
                any("Session Handover" in str(where) for where, _ in problems),
                "a name planted in a shipped skill must be reported",
            )
        finally:
            planted.write_text(original, encoding="utf-8")

    def test_repository_is_clean_right_now(self):
        problems = self.mod.check_all()
        self.assertEqual(
            [], problems,
            "shipped files carry personal detail: %s" % problems[:5],
        )


if __name__ == "__main__":
    unittest.main()
