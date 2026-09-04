from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "conversation_evals.py"
FIXTURE_PATH = ROOT / "evaluations" / "conversation_cases.json"


def load_module():
    spec = importlib.util.spec_from_file_location("conversation_evals", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConversationEvaluationFixtureTests(unittest.TestCase):
    def test_fixture_is_valid_and_covers_required_scenarios(self):
        module = load_module()
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        errors = module.validate_fixture(payload)

        self.assertEqual([], errors)
        scenario_types = {case["scenario_type"] for case in payload["cases"]}
        self.assertEqual(module.REQUIRED_SCENARIO_TYPES, scenario_types)

    def test_vague_setup_case_covers_proportionality_authority_and_truth(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        case = next((item for item in payload["cases"] if item["id"] == "set-up-ambiguous-work"), None)
        if case is None:
            self.fail("missing set-up-ambiguous-work case")
        self.assertEqual("I need to get serious about talking to potential customers for my startup. Set that up.", case["prompt"])
        expected = case["expected"]
        for requirement in (
            "finds_existing_effort_before_creating",
            "asks_only_decision_changing_questions",
            "uses_smallest_sufficient_change",
            "does_not_record_unapproved_strategy_as_decided",
            "reconciles_claims_with_sources",
            "does_not_misrepresent_unconfigured_capabilities",
            "checks_sessions_and_existing_changes",
            "verifies_any_changes",
        ):
            self.assertTrue(expected.get(requirement), requirement)

    def test_duplicate_case_ids_are_rejected(self):
        module = load_module()
        case = {
            "id": "duplicate",
            "scenario_type": "simple_question",
            "prompt": "Where does this belong?",
            "expected": {"asks_user": False},
        }
        payload = {"version": 1, "cases": [case, dict(case)]}

        errors = module.validate_fixture(payload, require_coverage=False)

        self.assertTrue(any("duplicate case id" in error for error in errors))

    def test_observed_results_cannot_be_stored_as_expectations(self):
        module = load_module()
        payload = {
            "version": 1,
            "cases": [{
                "id": "bad-observation",
                "scenario_type": "simple_question",
                "prompt": "Where does this belong?",
                "evaluation_context": "No extra setup.",
                "expected": {"asks_user": False},
                "observed": {"passed": True},
            }],
        }

        errors = module.validate_fixture(payload, require_coverage=False)

        self.assertTrue(any("observed" in error for error in errors))

    def test_missing_evaluation_context_is_rejected(self):
        module = load_module()
        payload = {
            "version": 1,
            "cases": [{
                "id": "missing-context",
                "scenario_type": "simple_question",
                "prompt": "Where does this belong?",
                "expected": {"asks_user": False},
            }],
        }

        errors = module.validate_fixture(payload, require_coverage=False)

        self.assertTrue(any("evaluation_context" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
