"""Unit tests for function_engine topic detection and solution plans."""

from __future__ import annotations

import pytest

from function_datasets import FUNCTION_TESTING_DATASET, FUNCTION_TRAINING_DATASET
from function_engine import detect_function_topic, try_build_function_plan


@pytest.mark.parametrize(
    ("expression", "topic"),
    [
        ("f(x)=2x+1|f(3)", "function_evaluation"),
        ("f(x)=x+1,g(x)=2x|f(g(2))", "function_composition"),
        ("f(x)=2x+1|finv(x)", "inverse_functions"),
        ("f(x)=2x+1|inv(x)", "inverse_functions"),
        ("f(x)=2x+1|f^-1(x)", "inverse_functions"),
        ("2^3*2^2", "exponential_functions"),
        ("log(8,2)", "logarithms"),
    ],
)
def test_detect_function_topic(expression: str, topic: str) -> None:
    assert detect_function_topic(expression) == topic


def test_lone_numeric_power_is_not_exponential_topic() -> None:
    assert detect_function_topic("2^3") is None


@pytest.mark.parametrize("problem", FUNCTION_TRAINING_DATASET, ids=lambda p: p["problem_id"])
def test_training_dataset_builds_plan(problem: dict) -> None:
    plan = try_build_function_plan(problem["expression"])
    assert plan.topic == problem["topic"]
    assert plan.final_answer == problem["correct_step"]


@pytest.mark.parametrize("problem", FUNCTION_TESTING_DATASET, ids=lambda p: p["problem_id"])
def test_testing_dataset_builds_plan(problem: dict) -> None:
    plan = try_build_function_plan(problem["expression"])
    assert plan.topic == problem["topic"]
    assert plan.final_answer == problem["correct_step"]


def test_nested_function_evaluation() -> None:
    plan = try_build_function_plan("f(x)=2x+1|f(f(1))")
    assert plan.final_answer == "7"


def test_triple_composition() -> None:
    plan = try_build_function_plan("f(x)=x+1,g(x)=2x-1,h(x)=x+2|f(g(h(1)))")
    assert plan.final_answer == "6"


def test_inv_notation_matches_finv() -> None:
    finv_plan = try_build_function_plan("f(x)=2x+1|finv(x)")
    inv_plan = try_build_function_plan("f(x)=2x+1|inv(x)")
    assert inv_plan.topic == "inverse_functions"
    assert inv_plan.final_answer == finv_plan.final_answer


def test_exponential_division() -> None:
    plan = try_build_function_plan("5^3/5^2")
    assert plan.steps == ["5^1", "5"]
    assert plan.final_answer == "5"
