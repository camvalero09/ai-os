from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINT_PATH = ROOT / "scripts/vault_lint.py"
TRACKER_WORKFLOW = ROOT / "Skills/Workflows/Start a Tracker.md"


def load_vault_lint():
    spec = importlib.util.spec_from_file_location("vault_lint_tracker_test", LINT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LINT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TrackerContractTests(unittest.TestCase):
    def test_tracker_workflow_requires_effort_metadata_and_next_action(self):
        text = TRACKER_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("A tracker is an effort with `status: active`", text)
        self.assertIn("its `next:` is whatever is due soonest", text)

    def test_lint_rejects_tracker_as_a_note_type(self):
        module = load_vault_lint()
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            system = vault / "System"
            (system / "template").mkdir(parents=True)
            note = vault / "Ideaverse/Efforts/Buyer Conversations.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                "---\n"
                "id: buyer-conversations\n"
                "type: tracker\n"
                "status: active\n"
                "domain: startup\n"
                "updated: 2026-09-04\n"
                "summary: Buyer conversations.\n"
                "---\n\n# Buyer conversations\n",
                encoding="utf-8",
            )
            setattr(module, "VAULT", vault)
            setattr(module, "SYSTEM", system)

            issues = module.check_status_vocabulary([note])

            self.assertTrue(any("type 'tracker'" in issue for issue in issues), issues)
            self.assertTrue(any("type: effort" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
