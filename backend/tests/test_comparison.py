"""Unit tests for StepValidator.comparison()."""
import pytest

from main import ParseError
from tests.equivalence_cases import EQUIVALENCE_CASES


@pytest.mark.parametrize(
    "row", EQUIVALENCE_CASES, ids=[f"case-{i}" for i in range(1, len(EQUIVALENCE_CASES) + 1)]
)
def test_comparison_golden_cases(validator, row):
    prob, exp, stu = row["problem"], row["expected"], row["student"]

    prob_result = validator.comparison(prob, exp)
    assert prob_result["is_equivalent"] is True

    stu_result = validator.comparison(stu, exp)
    assert stu_result["is_equivalent"] is False
    assert stu_result["structural_diff"] is not None


def test_comparison_identical_steps(validator):
    result = validator.comparison("2*x+6", "2*x+6")
    assert result["is_equivalent"] is True


def test_comparison_case_insensitive_variables(validator):
    """Lowercase student variables match uppercase problem symbols."""
    expected = "5X^5+25D*X+4"
    for student in ("4 + 25dx + 5 * x^5", "25xd + 5x^5 + 4", "4+25Dx+5x^5"):
        result = validator.comparison(student, expected)
        assert result["is_equivalent"] is True, f"Expected {student!r} to match"


def test_comparison_parse_failure(validator):
    with pytest.raises(ParseError):
        validator.comparison("2@3", "2*x")
