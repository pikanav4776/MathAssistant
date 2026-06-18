"""Tests for keyboard-math preprocessing before SymPy parsing."""

from __future__ import annotations

import pytest
from sympy import simplify, sympify

from expression_preprocess import display_expression, preprocess_for_sympy
from step_engine import build_solution_plan, canonical_step_display, detect_topic


def _sympy_equiv(expr_a: str, expr_b: str) -> bool:
    a = sympify(preprocess_for_sympy(expr_a))
    b = sympify(preprocess_for_sympy(expr_b))
    return simplify(a - b) == 0


@pytest.mark.parametrize(
    "raw,expected_fragment",
    [
        ("8x", "8*x"),
        ("22x", "22*x"),
        ("6x^2", "6*x**2"),
        ("(a)(b)", "(a)*(b)"),
        (") (", ")*("),
        ("504yx", "504*y*x"),
        ("504xy", "504*x*y"),
        ("2xy", "2*x*y"),
        ("yx", "y*x"),
    ],
    ids=[
        "digit-var",
        "multi-digit-var",
        "digit-var-power",
        "adjacent-parens",
        "spaced-parens",
        "digit-adjacent-vars",
        "digit-adjacent-vars-xy",
        "coeff-two-vars",
        "adjacent-vars",
    ],
)
def test_preprocess_implicit_multiplication(raw: str, expected_fragment: str) -> None:
    assert expected_fragment in preprocess_for_sympy(raw)


def test_preprocess_messy_foil_collapses_whitespace_and_parses() -> None:
    messy = "(8x + 6x^2 + 2 ) ( 8*x^2 + 22x +19)"
    cleaned = preprocess_for_sympy(messy)
    assert " " not in cleaned
    assert ")*(" in cleaned
    assert sympify(cleaned, evaluate=False) is not None


def test_messy_foil_detects_topic_and_builds_plan() -> None:
    messy = "(8x + 6x^2 + 2 ) ( 8*x^2 + 22x +19)"
    assert detect_topic(messy) == "foil"
    plan = build_solution_plan(messy)
    assert plan.topic == "foil"
    assert len(plan.steps) == 2
    assert plan.steps[0] != plan.final_answer
    compact = "(8x+6x^2+2)(8x^2+22x+19)"
    tidy_plan = build_solution_plan(compact)
    assert _sympy_equiv(plan.final_answer, tidy_plan.final_answer)


def test_display_expression_compact_keyboard_form() -> None:
    assert display_expression("8 * x + 6 * x**2") == "8x+6x^2"
    assert canonical_step_display("(8x + 6x^2 + 2 ) ( 8*x^2 + 22x +19)") == (
        "(8x+6x^2+2)(8x^2+22x+19)"
    )
