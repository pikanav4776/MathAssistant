"""Unit tests for trig_engine topic detection and solution plans."""

from __future__ import annotations

import pytest

from trig_datasets import TRIG_TESTING_DATASET, TRIG_TRAINING_DATASET
from trig_engine import detect_trig_topic, try_build_trig_plan


@pytest.mark.parametrize(
    ("expression", "topic"),
    [
        ("sin(pi/2)", "core_trig"),
        ("cos(0)", "core_trig"),
        ("tan(pi/4)", "core_trig"),
        ("sin(pi/6)+cos(pi/3)", "core_trig"),
        ("sin^2(x)+cos^2(x)", "basic_trig_identities"),
        ("2*sin^2(x)+2*cos^2(x)", "basic_trig_identities"),
        ("sin(x)=1/2", "trig_equations"),
        ("2*sin(x)=1", "trig_equations"),
    ],
)
def test_detect_trig_topic(expression: str, topic: str) -> None:
    assert detect_trig_topic(expression) == topic


@pytest.mark.parametrize("problem", TRIG_TRAINING_DATASET, ids=lambda p: p["problem_id"])
def test_training_dataset_builds_plan(problem: dict) -> None:
    plan = try_build_trig_plan(problem["expression"])
    assert plan.topic == problem["topic"]
    assert plan.final_answer == problem["correct_step"]


@pytest.mark.parametrize("problem", TRIG_TESTING_DATASET, ids=lambda p: p["problem_id"])
def test_testing_dataset_builds_plan(problem: dict) -> None:
    plan = try_build_trig_plan(problem["expression"])
    assert plan.topic == problem["topic"]
    assert plan.final_answer == problem["correct_step"]


def test_core_trig_multistep() -> None:
    plan = try_build_trig_plan("sin(pi/6)+cos(pi/6)")
    assert len(plan.steps) >= 2
    assert plan.final_answer == "1/2+sqrt(3)/2"


def test_identity_plan() -> None:
    plan = try_build_trig_plan("sin^2(x)+cos^2(x)")
    assert plan.topic == "basic_trig_identities"
    assert plan.final_answer == "1"
    assert plan.steps[0] == "sin^2(x)+cos^2(x)"


def test_trig_equation_plan() -> None:
    plan = try_build_trig_plan("sin(x)=1/2")
    assert plan.topic == "trig_equations"
    assert plan.final_answer == "x=pi/6,x=5pi/6"
    assert plan.steps[0] == "sin(x)=1/2"


def test_trig_equation_isolation_steps() -> None:
    plan = try_build_trig_plan("2*sin(x)=1")
    assert "sin(x)=1/2" in plan.steps
    assert plan.final_answer == "x=pi/6,x=5pi/6"
