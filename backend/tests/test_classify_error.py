"""Unit tests for StepValidator.classify_error() and targeted probes."""
import pytest

from tests.equivalence_cases import EQUIVALENCE_CASES
from tests.evaluation_dataset import EVALUATION_DATASET

# Mirrors run_phase1_checks.py — intuitive labels for golden rows
EXPECTED_CLASS_BY_INDEX = {
    1: "arithmetic_error",
    2: "distribution_error",
    3: "distribution_error",
    4: "arithmetic_error",
    5: "distribution_error",
    6: "arithmetic_error",
    7: "sign_error",
    8: "distribution_error",
    9: "distribution_error",
    10: "distribution_error",
}

CLASSIFICATION_PROBES = [
    ("sign_error", "2*x+3", "2*x-3"),
    ("arithmetic_error", "2*x+6", "2*x+5"),
    ("distribution_error", "2*x+2*y", "2*x"),
]


@pytest.mark.parametrize(
    "row,expected_type",
    [
        (EQUIVALENCE_CASES[i], EXPECTED_CLASS_BY_INDEX[i + 1])
        for i in range(len(EQUIVALENCE_CASES))
    ],
    ids=[f"golden-{i + 1}" for i in range(len(EQUIVALENCE_CASES))],
)
def test_classify_error_golden_cases(validator, row, expected_type):
    result = validator.validate(row["student"], row["expected"])
    assert result["is_equivalent"] is False
    assert result["error_classification"] is not None
    assert result["error_classification"]["error_type"] == expected_type


@pytest.mark.parametrize(
    "expected_type,expected_expr,student_expr",
    CLASSIFICATION_PROBES,
    ids=[p[0] for p in CLASSIFICATION_PROBES],
)
def test_classify_error_probes(validator, expected_type, expected_expr, student_expr):
    result = validator.validate(student_expr, expected_expr)
    got = (
        result["error_classification"]["error_type"]
        if result["error_classification"]
        else "correct"
    )
    assert got == expected_type


@pytest.mark.parametrize(
    "item",
    EVALUATION_DATASET,
    ids=[item["id"] for item in EVALUATION_DATASET],
)
def test_classify_error_evaluation_dataset(validator, item):
    """Each labeled wrong step in the Phase 2 dataset must classify correctly."""
    correct = item["correct"]
    for wrong in item["wrongs"]:
        result = validator.validate(wrong["expression"], correct)
        assert result["is_equivalent"] is False
        assert result["error_classification"] is not None
        assert result["error_classification"]["error_type"] == wrong["error_type"]
