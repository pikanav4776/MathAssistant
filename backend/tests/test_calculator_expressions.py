"""Calculator-built expressions — step parser support for constants, functions, comparisons."""
import pytest
from sympy import E, Mod, pi, sqrt, Symbol
from sympy.core.relational import LessThan

from main import StepValidator, _handle_step_validation, StepInput
from step_engine import UnsupportedProblemError, build_solution_plan


@pytest.fixture
def validator() -> StepValidator:
    return StepValidator()


def test_parser_accepts_pi_e_tau_constants(validator: StepValidator) -> None:
    expr = validator.parser("pi + e + tau")
    assert expr.free_symbols == set()
    normalized = validator.normalize(expr)
    assert normalized.equals(pi + E + 2 * pi)


def test_parser_accepts_sqrt(validator: StepValidator) -> None:
    x = Symbol("x")
    expr = validator.parser("sqrt(x)")
    assert expr.equals(sqrt(x))


def test_parser_accepts_mod(validator: StepValidator) -> None:
    a = Symbol("a")
    expr = validator.parser("mod(a, 3)")
    assert expr.equals(Mod(a, 3))


def test_parser_accepts_relational_comparison(validator: StepValidator) -> None:
    x = Symbol("x")
    expr = validator.parser("x <= 5")
    assert isinstance(expr, LessThan)
    assert expr.lhs == x
    assert expr.rhs == 5


def test_relational_equivalence_via_validate(validator: StepValidator) -> None:
    result = validator.validate("x <= 5", "x <= 5")
    assert result["is_equivalent"] is True
    assert result["error_classification"] is None


def test_api_calculator_expressions_do_not_crash() -> None:
    for step in ("pi + e", "sqrt(x)", "mod(a, 3)", "x <= 5"):
        body = _handle_step_validation(
            StepInput(session_id="calc-test", step=step, expected=step)
        )
        assert body.error_classification is None or body.error_classification["error_type"] not in (
            "engine_error",
        )


def test_start_session_still_rejects_calculator_advanced_syntax() -> None:
    with pytest.raises(UnsupportedProblemError):
        build_solution_plan("sqrt(x)")

    with pytest.raises(UnsupportedProblemError):
        build_solution_plan("x <= 5")
