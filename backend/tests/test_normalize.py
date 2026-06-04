"""Unit tests for StepValidator.normalize()."""
import pytest
from sympy import simplify

from tests.equivalence_cases import EQUIVALENCE_CASES

NORMALIZE_EQUIVALENCE_CASES = [
    {"id": "distribute-scalar", "a": "2*(x+3)", "b": "2*x+6"},
    {"id": "combine-like-x", "a": "x+x", "b": "2*x"},
    {"id": "combine-like-mixed", "a": "4*a-2*a+6*a", "b": "8*a"},
]


@pytest.mark.parametrize(
    "case", NORMALIZE_EQUIVALENCE_CASES, ids=[c["id"] for c in NORMALIZE_EQUIVALENCE_CASES]
)
def test_normalize_equivalence(validator, case):
    left = validator.normalize(validator.parser(case["a"]))
    right = validator.normalize(validator.parser(case["b"]))
    assert simplify(left - right) == 0


@pytest.mark.parametrize(
    "row", EQUIVALENCE_CASES, ids=[f"golden-{i}" for i in range(1, len(EQUIVALENCE_CASES) + 1)]
)
def test_normalize_problem_matches_expected(validator, row):
    """Each benchmark problem should normalize to its labeled correct step."""
    problem = validator.normalize(validator.parser(row["problem"]))
    expected = validator.normalize(validator.parser(row["expected"]))
    assert simplify(problem - expected) == 0
