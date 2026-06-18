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


def test_comparison_parse_failure(validator):
    with pytest.raises(ParseError):
        validator.comparison("2@3", "2*x")
