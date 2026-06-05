"""Unit tests for StepValidator.parser()."""
import pytest
from sympy import simplify

from main import DivisionByZeroError, InvalidFormatError, MalformedSyntaxError, ParseError, UndefinedMathError
from tests.parser_cases import PARSER_INVALID_CASES, PARSER_VALID_CASES


@pytest.mark.parametrize("case", PARSER_VALID_CASES, ids=[c["id"] for c in PARSER_VALID_CASES])
def test_parser_accepts_valid_input(validator, case):
    expr = validator.parser(case["expression"])
    assert expr is not None

    if "equivalent_to" in case:
        a = validator.normalize(expr)
        b = validator.normalize(validator.parser(case["equivalent_to"]))
        assert simplify(a - b) == 0


@pytest.mark.parametrize(
    "case", PARSER_INVALID_CASES, ids=[c["id"] for c in PARSER_INVALID_CASES]
)
def test_parser_rejects_invalid_input(validator, case):
    expected = {
        "invalid_format": InvalidFormatError,
        "division_by_zero": DivisionByZeroError,
        "undefined_math": UndefinedMathError,
    }.get(case.get("error_type"), MalformedSyntaxError)
    with pytest.raises(expected):
        validator.parser(case["expression"])
