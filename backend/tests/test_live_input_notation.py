"""Live student notation — parse and validate without evaluation failures."""

from __future__ import annotations

import pytest

from main import StepInput, StepValidator, _handle_step_validation

# Calculator-built and keyboard-style strings students actually type
LIVE_PARSE_CASES = [
    "2(x+3)",
    "2*(x+3)",
    "2x+6",
    "x^2+2*x+1",
    "x**2+2*x+1",
    "(x+1)^2",
    "(x+1)**2",
    "pi+e",
    "sqrt(x)",
    "mod(a,3)",
]

NOTATION_EQUIVALENCE_CASES = [
    ("x^2+1", "x**2+1"),
    ("2(x+3)", "2*(x+3)"),
    ("X+2", "x+2"),
    ("2X+6", "2x+6"),
]


@pytest.mark.parametrize("expression", LIVE_PARSE_CASES)
def test_live_input_parses_without_error(validator: StepValidator, expression: str) -> None:
    expr = validator.parser(expression)
    normalized = validator.normalize(expr)
    assert normalized is not None


@pytest.mark.parametrize("student,expected", NOTATION_EQUIVALENCE_CASES)
def test_live_notation_equivalence(
    validator: StepValidator, student: str, expected: str
) -> None:
    result = validator.validate(student, expected)
    assert result["is_equivalent"] is True
    assert result["error_classification"] is None


def test_calculator_built_distribution_step_validates() -> None:
    body = _handle_step_validation(
        StepInput(session_id="live-notation", step="2*x+6", expected="2*x+6")
    )
    assert body.is_equivalent is True
    assert body.error_classification is None


def test_python_exponent_via_api_matches_caret() -> None:
    caret = _handle_step_validation(
        StepInput(session_id="live-notation", step="x^2+1", expected="x^2+1")
    )
    python_style = _handle_step_validation(
        StepInput(session_id="live-notation", step="x**2+1", expected="x^2+1")
    )
    assert caret.is_equivalent is True
    assert python_style.is_equivalent is True
