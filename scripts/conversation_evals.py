#!/usr/bin/env python3
"""Validate AI OS conversational evaluation fixtures.

This does not run or score an agent. It checks that the human-run evaluation
contract is complete, neutral, and free of fabricated observations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_SCENARIO_TYPES = {
    "simple_question",
    "reversible_edit",
    "external_action",
    "resume_effort",
    "audience_writing",
    "capture_information",
    "structural_change",
    "missing_capability",
    "cross_model_resume",
    "collision_detection",
}


def validate_fixture(payload: Any, *, require_coverage: bool = True) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["fixture must be a JSON object"]
    if payload.get("version") != 1:
        errors.append("version must be 1")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a non-empty list"]

    seen_ids: set[str] = set()
    seen_types: set[str] = set()
    for index, case in enumerate(cases):
        label = f"case {index + 1}"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{label} needs a non-empty id")
        elif case_id in seen_ids:
            errors.append(f"duplicate case id: {case_id}")
        else:
            seen_ids.add(case_id)

        scenario_type = case.get("scenario_type")
        if scenario_type not in REQUIRED_SCENARIO_TYPES:
            errors.append(f"{label} has unsupported scenario_type: {scenario_type}")
        else:
            seen_types.add(scenario_type)

        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{label} needs a non-empty prompt")
        evaluation_context = case.get("evaluation_context")
        if not isinstance(evaluation_context, str) or not evaluation_context.strip():
            errors.append(f"{label} needs a non-empty evaluation_context")
        expected = case.get("expected")
        if not isinstance(expected, dict) or not expected:
            errors.append(f"{label} needs a non-empty expected object")
        if "observed" in case:
            errors.append(f"{label} must not contain observed results; record those in a separate run artifact")

    if require_coverage:
        missing = sorted(REQUIRED_SCENARIO_TYPES - seen_types)
        extra = sorted(seen_types - REQUIRED_SCENARIO_TYPES)
        if missing:
            errors.append("missing scenario types: " + ", ".join(missing))
        if extra:
            errors.append("unexpected scenario types: " + ", ".join(extra))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "evaluations" / "conversation_cases.json",
    )
    args = parser.parse_args()
    try:
        payload = json.loads(args.fixture.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    errors = validate_fixture(payload)
    if errors:
        print("Conversation evaluation fixture: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Conversation evaluation fixture: PASS ({len(payload['cases'])} cases)")
    print("This validates the evaluation contract only; no agent behavior was run or scored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
