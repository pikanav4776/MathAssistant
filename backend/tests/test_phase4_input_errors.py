"""Phase 4 — input error categories and safe API responses."""
import pytest

from main import (
    DivisionByZeroError,
    MalformedSyntaxError,
    StepInput,
    UndefinedMathError,
    _handle_step_validation,
)


def test_valid_expression_no_input_error(validator):
    result = validator.validate("2*x+6", "2*x+6")
    assert result["is_equivalent"] is True
    assert result["error_classification"] is None


def test_parser_rejects_division_by_zero_literal(validator):
    with pytest.raises(DivisionByZeroError):
        validator.parser("1/0")


def test_parser_rejects_log_zero_text(validator):
    with pytest.raises(UndefinedMathError):
        validator.parser("log(0)")


def test_parser_rejects_malformed_syntax(validator):
    with pytest.raises(MalformedSyntaxError):
        validator.parser("2*/3")


def test_parser_accepts_caret_and_python_exponent_formats(validator):
    caret = validator.parser("x^2")
    python_style = validator.parser("x**2")
    assert validator.normalize(caret) == validator.normalize(python_style)


def _submit(step: str, expected: str = "2*x+6"):
    return _handle_step_validation(
        StepInput(session_id="t", step=step, expected=expected)
    )


def test_api_division_by_zero_safe_response():
    body = _submit("1/0")
    assert body.error_classification["error_type"] == "division_by_zero"
    assert "Sympify" not in body.hint
    assert "Traceback" not in body.hint


def test_api_malformed_syntax_safe_response():
    body = _submit("2*/3")
    assert body.error_classification["error_type"] == "malformed_syntax"
    assert "Sympify" not in body.hint


def test_api_undefined_math_safe_response():
    body = _submit("log(0)")
    assert body.error_classification["error_type"] == "undefined_math"


def test_api_python_exponent_accepted():
    body = _submit("x**2", expected="x**2")
    assert body.is_equivalent is True
    assert body.error_classification is None


def test_api_garbage_symbol_safe_response():
    body = _submit("2@3")
    assert body.error_classification["error_type"] in (
        "malformed_syntax",
        "undefined_symbol",
    )
    assert "exception" not in body.hint.lower()
