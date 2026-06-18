"""Multi-hop canonical path generation in step_engine."""

from __future__ import annotations

import pytest
from sympy import simplify, sympify

from expression_preprocess import preprocess_for_sympy
from step_engine import build_solution_plan


def _sympy_equiv(expr_a: str, expr_b: str) -> bool:
    a = sympify(preprocess_for_sympy(expr_a))
    b = sympify(preprocess_for_sympy(expr_b))
    return simplify(a - b) == 0


def test_multihop_2x_plus_3_plus_4() -> None:
    plan = build_solution_plan("2(x+3)+4")
    assert len(plan.steps) >= 2
    assert plan.steps[0] == "2x+6+4"
    assert _sympy_equiv(plan.steps[-1], "2x+10")
    assert plan.final_answer == plan.steps[-1]


@pytest.mark.parametrize(
    "expression,intermediate,final_answer",
    [
        ("3(x-2)+5", "3x-6+5", "3x-1"),
        ("-2(x+1)+3", "-2x-2+3", "-2x+1"),
    ],
    ids=["dist-plus-constant", "neg-dist-plus-constant"],
)
def test_multihop_distribution_plus_constant(
    expression: str, intermediate: str, final_answer: str
) -> None:
    plan = build_solution_plan(expression)
    assert len(plan.steps) == 2
    assert _sympy_equiv(plan.steps[0], intermediate)
    assert _sympy_equiv(plan.final_answer, final_answer)


def test_single_hop_distribution_unchanged() -> None:
    plan = build_solution_plan("2(x+3)")
    assert len(plan.steps) == 1
    assert _sympy_equiv(plan.final_answer, "2x+6")


def test_single_hop_linear_steps_unchanged() -> None:
    plan = build_solution_plan("5x+3-2x")
    assert len(plan.steps) == 1
    assert _sympy_equiv(plan.final_answer, "3x+3")


def test_multihop_foil_plus_constant() -> None:
    plan = build_solution_plan("(x+1)(x+2)+3")
    assert len(plan.steps) >= 2
    assert _sympy_equiv(plan.steps[0], "x^2+3x+2+3")
    assert _sympy_equiv(plan.final_answer, "x^2+3x+5")
