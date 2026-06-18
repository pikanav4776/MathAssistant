"""Commit 2 — step_engine topic detection, single-hop plans, and rejection matrix."""

from __future__ import annotations

import pytest
from sympy import simplify, sympify

from expression_preprocess import preprocess_for_sympy
from main import StepValidator
from step_engine import (
    UnsupportedProblemError,
    build_solution_plan,
    detect_topic,
    reject_if_unsupported,
)


def _sympy_equiv(expr_a: str, expr_b: str) -> bool:
    a = sympify(preprocess_for_sympy(expr_a))
    b = sympify(preprocess_for_sympy(expr_b))
    return simplify(a - b) == 0


def _assert_plan_matches(expression: str, expected_final: str, *, topic: str | None = None) -> None:
    plan = build_solution_plan(expression)
    assert plan.subject == "algebra"
    assert len(plan.steps) == 1
    assert plan.steps[0] == plan.final_answer
    if topic is not None:
        assert plan.topic == topic
    assert _sympy_equiv(plan.final_answer, expected_final), (
        f"{expression!r} -> {plan.final_answer!r}, expected {expected_final!r}"
    )


# ── 1. Topic detection (~10) ────────────────────────────────────────────────

@pytest.mark.parametrize(
    "expression,topic",
    [
        ("2(x+3)", "distribution"),
        ("3(x-4)", "distribution"),
        ("-2(x+1)", "distribution"),
        ("(x+2)(x+3)", "foil"),
        ("(x+1)(x-5)", "foil"),
        ("(2x+1)(x+4)", "foil"),
        ("5x+3-2x", "linear_steps"),
        ("x^2+x+1", "linear_steps"),
        ("3x-x+4", "linear_steps"),
        ("x^2", "simplification"),
        ("-x", "simplification"),
        ("2x^3", "simplification"),
    ],
    ids=[
        "dist-2(x+3)",
        "dist-3(x-4)",
        "dist-neg-coeff",
        "foil-plus-plus",
        "foil-plus-minus",
        "foil-coeff-x",
        "linear-combine",
        "linear-poly",
        "linear-cancel",
        "simp-power",
        "simp-neg-var",
        "simp-cubic",
    ],
)
def test_detect_topic_supported(expression: str, topic: str) -> None:
    assert detect_topic(expression) == topic


@pytest.mark.parametrize(
    "expression",
    [
        "x+3-2x+1",
        "-(x+4)+2x",
    ],
    ids=["signed-combine", "neg-distribute-then-combine"],
)
def test_detect_topic_linear_steps_for_signed_simplification_shapes(expression: str) -> None:
    """Evaluation labels vary; engine classifies multi-term sums as linear_steps."""
    assert detect_topic(expression) == "linear_steps"


# ── 2. Single-hop solution plans (~10) ──────────────────────────────────────

@pytest.mark.parametrize(
    "expression,expected_final,topic",
    [
        ("2(x+3)", "2x+6", "distribution"),
        ("3(x-4)", "3x-12", "distribution"),
        ("(x+2)(x+3)", "x^2+5x+6", "foil"),
        ("(x+2)(x-3)", "x^2-x-6", "foil"),
        ("5x+3-2x", "3x+3", "linear_steps"),
        ("4(2x+5)", "8x+20", "distribution"),
        ("(x-4)(x-1)", "x^2-5x+4", "foil"),
        ("3x-x+4", "2x+4", "linear_steps"),
        ("x+3-2x+1", "-x+4", "linear_steps"),
        ("-(x+4)+2x", "x-4", "linear_steps"),
    ],
    ids=[
        "dist-2(x+3)",
        "dist-3(x-4)",
        "foil-standard",
        "foil-mixed-sign",
        "linear-5x+3-2x",
        "dist-eval-4(2x+5)",
        "foil-eval-dexp_009",
        "linear-eval-lin_001",
        "signed-eval-sign_001",
        "signed-eval-sign_003",
    ],
)
def test_build_solution_plan_single_hop(expression: str, expected_final: str, topic: str) -> None:
    _assert_plan_matches(expression, expected_final, topic=topic)


def test_build_solution_plan_single_hop_structure() -> None:
    plan = build_solution_plan("2(x+3)")
    assert plan.subject == "algebra"
    assert plan.topic == "distribution"
    assert len(plan.steps) == 1
    assert plan.steps[0] == plan.final_answer
    assert _sympy_equiv(plan.final_answer, "2x+6")


# ── 3. Exponent equivalence (~6) ────────────────────────────────────────────

@pytest.mark.parametrize(
    "caret_form,python_form",
    [
        ("x^2+1", "x**2+1"),
        ("(x+1)^2", "(x+1)**2"),
        ("2x^3", "2x**3"),
    ],
    ids=["quadratic-term", "binomial-square", "cubic-coeff"],
)
def test_exponent_forms_produce_equivalent_plans(caret_form: str, python_form: str) -> None:
    caret_plan = build_solution_plan(caret_form)
    python_plan = build_solution_plan(python_form)
    assert caret_plan.topic == python_plan.topic
    assert caret_plan.steps == python_plan.steps
    assert caret_plan.final_answer == python_plan.final_answer
    assert _sympy_equiv(caret_plan.final_answer, python_plan.final_answer)


@pytest.mark.parametrize(
    "caret_form,python_form",
    [
        ("x^2+1", "x**2+1"),
        ("(x+1)^2", "(x+1)**2"),
        ("2x^3", "2x**3"),
    ],
    ids=["validator-quadratic", "validator-binomial", "validator-cubic"],
)
def test_step_validator_parser_normalized_exponent_forms_match(
    validator: StepValidator, caret_form: str, python_form: str
) -> None:
    caret_norm = validator.normalize(validator.parser(caret_form))
    python_norm = validator.normalize(validator.parser(python_form))
    assert simplify(caret_norm - python_norm) == 0


# ── 4. Rejection matrix (~12) ───────────────────────────────────────────────

@pytest.mark.parametrize(
    "expression,reason_fragment",
    [
        ("2x+3=7", "Equations"),
        ("x+1=0", "Equations"),
        ("x>2", "inequalities"),
        ("x<5", "inequalities"),
        ("x>=3", "inequalities"),
        ("sqrt(x)", "Function"),
        ("sin(x)", "Function"),
        ("log(x)", "Function"),
        ("cos(2x)", "Function"),
        ("", "empty"),
        ("2@@3", "keyboard-typable"),
        ("2@3", "keyboard-typable"),
        ("(x+1)(x+2)(x+3)", "Unsupported problem shape"),
        ("5", "Unsupported problem shape"),
    ],
    ids=[
        "equation-linear",
        "equation-zero",
        "ineq-gt",
        "ineq-lt",
        "ineq-gte",
        "func-sqrt",
        "func-sin",
        "func-log",
        "func-cos",
        "empty",
        "garbage-double-at",
        "garbage-at",
        "triple-binomial",
        "constant-literal",
    ],
)
def test_build_solution_plan_rejects_unsupported(expression: str, reason_fragment: str) -> None:
    with pytest.raises(UnsupportedProblemError) as exc_info:
        build_solution_plan(expression)
    assert reason_fragment.lower() in str(exc_info.value).lower()


# ── 5. reject_if_unsupported (~3) ───────────────────────────────────────────

def test_reject_if_unsupported_accepts_supported_distribution() -> None:
    reject_if_unsupported("2(x+3)")


def test_reject_if_unsupported_rejects_equation() -> None:
    with pytest.raises(UnsupportedProblemError, match="Equations"):
        reject_if_unsupported("2x+3=7")


def test_reject_if_unsupported_rejects_constant_only() -> None:
    with pytest.raises(UnsupportedProblemError, match="Unsupported problem shape"):
        reject_if_unsupported("5")


# ── 6. Regression guards ──────────────────────────────────────────────────

def test_regression_2x_plus_3_plus_4_is_multihop() -> None:
    """2(x+3)+4 expands then combines like terms in two hops."""
    plan = build_solution_plan("2(x+3)+4")
    assert plan.topic == "linear_steps"
    assert len(plan.steps) == 2
    assert plan.steps[0] == "2x+6+4"
    assert plan.final_answer == plan.steps[-1]
    assert _sympy_equiv(plan.final_answer, "2x+10")
