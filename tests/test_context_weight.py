from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_views.py"
RULES = ROOT / "Agent Rules.md"

# A loader exists to route to its canonical note. Every word beyond that is
# duplicated in each generated file and read again on every trigger.
MAX_LOADER_BODY_WORDS = 40


def load_module():
    spec = importlib.util.spec_from_file_location("build_views_weight_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def card() -> str:
    text = RULES.read_text(encoding="utf-8")
    return text.split("<!-- BEGIN CARD -->", 1)[1].split("<!-- END CARD -->", 1)[0]


class ContextWeightTests(unittest.TestCase):
    def sample_loader(self) -> str:
        return load_module().render_loader(
            {
                "id": "example-skill",
                "summary": "Works through a decision: options, tradeoffs, reversibility, next step",
                "triggers": "work through a decision, compare options",
                "_title": "Example Skill",
                "_rel_md": "System/Skills/Workflows/Example Skill.md",
            }
        )

    def test_loader_body_stays_small(self):
        body = self.sample_loader().split("---", 2)[2]
        words = len(body.split())
        self.assertLessEqual(
            words, MAX_LOADER_BODY_WORDS,
            f"loader body is {words} words; it only has to name the note to read",
        )

    def test_loader_still_routes_to_its_canonical_note(self):
        loader = self.sample_loader()
        module = load_module()
        self.assertIn("System/Skills/Workflows/Example Skill.md", loader)
        self.assertIn(module.LOADER_MARK, loader)
        self.assertTrue(re.search(r"^description: ", loader, re.MULTILINE))

    def test_rules_do_not_relitigate_status_labels(self):
        text = card()
        self.assertNotIn("Cannot verify", text)
        self.assertNotIn("Ordinary conversation does not require a status label", text)
        self.assertIn("Report what materially changed", text)
        self.assertIn("only when they block completion or require the owner's decision", text)

    def test_rules_do_not_prescribe_formatting_formula(self):
        self.assertNotIn("not by formula", card())

    def test_skill_description_procedure_is_not_always_loaded(self):
        self.assertNotIn("Skill descriptions use third person", card())


if __name__ == "__main__":
    unittest.main()
