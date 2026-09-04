"""A release that changes no rule text must still pass the upgrade gate.

The gate proved regeneration by asserting the generated adapters and skill
loaders differ from the baseline's. That holds only for releases that edit
rules or skills. v2.30 changed one script and nothing else, so identical
artifacts were the correct outcome and the gate called it a failure.

Sameness is not the property worth checking. Currency is: after upgrading,
build_views.py --check must report no drift.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "release_simulation.py"


def load():
    spec = importlib.util.spec_from_file_location("release_sim_currency_test", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GeneratedArtifactsAreCheckedForCurrencyTests(unittest.TestCase):
    def setUp(self):
        self.source = MODULE.read_text(encoding="utf-8")
        self.mod = load()

    def test_upgrade_does_not_require_artifacts_to_change(self):
        self.assertNotIn(
            "candidate_skill_loaders != baseline_skill_loaders", self.source,
            "a release touching only a script leaves loaders byte-identical, "
            "and that is correct rather than a failed upgrade",
        )
        self.assertNotIn(
            "candidate_portable_skill_loaders != baseline_portable_skill_loaders",
            self.source,
        )
        self.assertNotIn("candidate_entries != baseline_entries", self.source)

    def test_currency_helper_exists_and_uses_the_drift_check(self):
        self.assertTrue(
            hasattr(self.mod, "generated_artifacts_current"),
            "the gate needs a positive check that regeneration produced current output",
        )
        self.assertIn('"scripts/build_views.py"), "--check"', self.source)

    def test_upgrade_still_reports_the_loader_fields(self):
        for field in ("adapters_rebuilt", "skill_loaders_rebuilt",
                      "portable_skill_loaders_rebuilt"):
            self.assertIn(f'"{field}"', self.source,
                          "reported fields stay, so the release record keeps its shape")

    def test_adapters_are_still_structurally_verified(self):
        self.assertIn("verify_adapters(vault)", self.source)


if __name__ == "__main__":
    unittest.main()
