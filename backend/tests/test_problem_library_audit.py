"""Audit tests for the seeded 72-problem library."""

from __future__ import annotations

import pytest
from step_engine import build_solution_plan, canonical_step_display

from evaluation_dataset import EVALUATION_DATASET
from main import StepValidator


@pytest.mark.parametrize("problem", EVALUATION_DATASET, ids=lambda p: p["problem_id"])
def test_library_problem_builds_solution_plan(problem: dict) -> None:
    plan = build_solution_plan(problem["expression"])
    assert plan.steps
    assert plan.final_answer


@pytest.mark.parametrize("problem", EVALUATION_DATASET, ids=lambda p: p["problem_id"])
def test_library_expected_final_matches_engine(problem: dict, validator: StepValidator) -> None:
    plan = build_solution_plan(problem["expression"])
    expected = canonical_step_display(problem["correct_step"])
    engine_final = canonical_step_display(plan.final_answer)
    assert expected == engine_final, (
        f"{problem['problem_id']}: stored={expected!r} engine={engine_final!r}"
    )
    result = validator.validate(problem["correct_step"], plan.final_answer)
    assert result["is_equivalent"] is True


def test_library_covers_all_topics_and_difficulties() -> None:
    topics = {problem["topic"] for problem in EVALUATION_DATASET}
    difficulties = {problem["difficulty"] for problem in EVALUATION_DATASET}
    assert topics == {
        "distribution",
        "simplification",
        "double_expansion",
        "linear_steps",
        "multihop",
    }
    assert difficulties == {"easy", "medium", "hard"}
    assert len(EVALUATION_DATASET) == 72
