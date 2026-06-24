import pytest

from calculator_answer import CalculatorAnswerError, compute_calculator_answer


def test_answer_simplifies_expression() -> None:
    assert compute_calculator_answer("2(x+3)") == "2x+6"


def test_answer_solves_linear_equation() -> None:
    assert compute_calculator_answer("2x+5=9") == "x=2"


def test_answer_solves_quadratic_equation() -> None:
    answer = compute_calculator_answer("x^2-5x+6=0")
    assert answer in {"x=2, x=3", "x=3, x=2"}


def test_answer_rejects_comparisons() -> None:
    with pytest.raises(CalculatorAnswerError):
        compute_calculator_answer("x<=5")


def test_answer_rejects_empty_input() -> None:
    with pytest.raises(CalculatorAnswerError, match="empty"):
        compute_calculator_answer("   ")
