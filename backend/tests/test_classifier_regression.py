"""Regression tests for polynomial classifier fixes (Phase 6).

Historically, arith_002, lin_009, and lin_010 wrong answers were mislabeled as
distribution_error when terms shared the same monomial basis but differed in
sign or coefficient. The _is_distribution_error guard must keep these as
sign_error or arithmetic_error.
"""

from __future__ import annotations

import pytest

REGRESSION_CASES = [
    pytest.param(
        "arith_002",
        "7x^2+x",
        "7x^2-x",
        "sign_error",
        id="arith_002-sign",
    ),
    pytest.param(
        "arith_002",
        "6x^2-x",
        "7x^2-x",
        "arithmetic_error",
        id="arith_002-arithmetic",
    ),
    pytest.param(
        "lin_009",
        "-x^2-x",
        "x^2+x",
        "sign_error",
        id="lin_009-sign",
    ),
    pytest.param(
        "lin_010",
        "-3x^2-3x",
        "3x^2+3x",
        "sign_error",
        id="lin_010-sign",
    ),
]


@pytest.mark.parametrize(
    "problem_id,wrong_step,correct_step,expected_type",
    REGRESSION_CASES,
)
def test_polynomial_classifier_regression(
    validator,
    problem_id: str,
    wrong_step: str,
    correct_step: str,
    expected_type: str,
) -> None:
    result = validator.validate(wrong_step, correct_step)
    assert result["is_equivalent"] is False, problem_id
    assert result["error_classification"] is not None
    assert result["error_classification"]["error_type"] == expected_type
