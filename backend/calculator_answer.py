"""Compute simplified or solved answers for calculator Ans requests."""

from __future__ import annotations

import re

from sympy import E, Eq, Mod, pi, solve, sqrt, sympify
from sympy.core.sympify import SympifyError

from expression_preprocess import contains_text_like_input, display_expression, preprocess_for_sympy
from step_engine import UnsupportedProblemError, _normalize_expr, build_solution_plan

_SYMPY_LOCALS = {
    "e": E,
    "E": E,
    "pi": pi,
    "tau": 2 * pi,
    "mod": Mod,
    "sqrt": sqrt,
}

_COMPARISON_OPS = ("<=", ">=", "==", "!=", "<", ">")


class CalculatorAnswerError(ValueError):
    """User-facing calculator answer failure."""


def _is_simple_equation(expression: str) -> bool:
    if any(op in expression for op in _COMPARISON_OPS):
        return False
    return "=" in expression


def _parse_algebra(expression: str):
    sympy_ready = preprocess_for_sympy(expression.strip())
    try:
        return sympify(sympy_ready, locals=_SYMPY_LOCALS)
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        raise CalculatorAnswerError(
            "That expression could not be read. Check your notation."
        ) from exc


def _answer_for_equation(expression: str) -> str:
    lhs_text, rhs_text = expression.split("=", 1)
    if not lhs_text.strip() or not rhs_text.strip():
        raise CalculatorAnswerError("Enter both sides of the equation around =.")

    lhs = _parse_algebra(lhs_text)
    rhs = _parse_algebra(rhs_text)
    equation = Eq(lhs, rhs)
    symbols = sorted(equation.free_symbols, key=lambda symbol: str(symbol).lower())

    if not symbols:
        if lhs.equals(rhs):
            return "True"
        raise CalculatorAnswerError("No variable to solve for.")

    symbol = symbols[0]
    solutions = solve(equation, symbol)
    if not solutions:
        raise CalculatorAnswerError("No solution found for this equation.")

    formatted = [
        display_expression(f"{symbol}={solution}") for solution in solutions
    ]
    return ", ".join(formatted)


def _answer_for_expression(expression: str) -> str:
    try:
        plan = build_solution_plan(expression)
        return display_expression(plan.final_answer)
    except UnsupportedProblemError:
        expr = _parse_algebra(expression)
        normalized = _normalize_expr(expr)
        return display_expression(str(normalized))


def compute_calculator_answer(expression: str) -> str:
    cleaned = re.sub(r"\s+", " ", expression.strip())
    if not cleaned:
        raise CalculatorAnswerError("Expression is empty.")
    if contains_text_like_input(cleaned):
        raise CalculatorAnswerError(
            "Plain text and word-like input are not allowed. Use math notation."
        )
    if any(op in cleaned for op in _COMPARISON_OPS):
        raise CalculatorAnswerError(
            "Comparisons are not supported. Use a single = for equations."
        )

    if _is_simple_equation(cleaned):
        return _answer_for_equation(cleaned)
    return _answer_for_expression(cleaned)
