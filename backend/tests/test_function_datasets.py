"""Audit tests for function training and testing datasets."""

from __future__ import annotations

from collections import Counter

import pytest

from function_datasets import (
    FUNCTION_TESTING_DATASET,
    FUNCTION_TOPICS,
    FUNCTION_TRAINING_DATASET,
)
from step_engine import build_solution_plan, canonical_step_display
from main import StepValidator


def _assert_difficulty_split(dataset: list[dict], label: str) -> None:
    counts = Counter(problem["difficulty"] for problem in dataset)
    assert counts["easy"] == 3, f"{label} easy count"
    assert counts["medium"] == 3, f"{label} medium count"
    assert counts["hard"] == 4, f"{label} hard count"


@pytest.mark.parametrize("topic", FUNCTION_TOPICS)
def test_training_topic_has_ten_problems(topic: str) -> None:
    items = [problem for problem in FUNCTION_TRAINING_DATASET if problem["topic"] == topic]
    assert len(items) == 10
    _assert_difficulty_split(items, f"training:{topic}")


@pytest.mark.parametrize("topic", FUNCTION_TOPICS)
def test_testing_topic_has_ten_problems(topic: str) -> None:
    items = [problem for problem in FUNCTION_TESTING_DATASET if problem["topic"] == topic]
    assert len(items) == 10
    _assert_difficulty_split(items, f"testing:{topic}")


@pytest.mark.parametrize("problem", FUNCTION_TRAINING_DATASET, ids=lambda p: p["problem_id"])
def test_training_problem_matches_engine(problem: dict, validator: StepValidator) -> None:
    plan = build_solution_plan(problem["expression"])
    expected = canonical_step_display(problem["correct_step"])
    engine_final = canonical_step_display(plan.final_answer)
    assert expected == engine_final
    result = validator.validate(problem["correct_step"], plan.final_answer)
    assert result["is_equivalent"] is True


@pytest.mark.parametrize("problem", FUNCTION_TESTING_DATASET, ids=lambda p: p["problem_id"])
def test_testing_problem_matches_engine(problem: dict, validator: StepValidator) -> None:
    plan = build_solution_plan(problem["expression"])
    expected = canonical_step_display(problem["correct_step"])
    engine_final = canonical_step_display(plan.final_answer)
    assert expected == engine_final
    result = validator.validate(problem["correct_step"], plan.final_answer)
    assert result["is_equivalent"] is True
