"""Unit tests for StepValidator.validate() — full pipeline."""
import pytest

from main import ParseError
from tests.equivalence_cases import EQUIVALENCE_CASES


def test_validate_correct_step(validator):
    result = validator.validate("2*x+6", "2*x+6")
    assert result["is_equivalent"] is True
    assert result["error_classification"] is None
    assert "Correct" in result["hint"]


@pytest.mark.parametrize(
    "row", EQUIVALENCE_CASES, ids=[f"wrong-{i}" for i in range(1, len(EQUIVALENCE_CASES) + 1)]
)
def test_validate_detects_incorrect_golden_steps(validator, row):
    result = validator.validate(row["student"], row["expected"])
    assert result["is_equivalent"] is False
    assert result["error_classification"] is not None
    assert result["hint"]
    assert result["structural_diff"] is not None


def test_validate_includes_structural_diff_on_failure(validator):
    result = validator.validate("2*x+3", "2*x+6")
    assert result["is_equivalent"] is False
    assert "coeff_diff" in result["structural_diff"]


def test_validate_parse_error_bubbles(validator):
    with pytest.raises(ParseError):
        validator.validate("2@3", "2*x")
