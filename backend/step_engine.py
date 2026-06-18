from __future__ import annotations

from dataclasses import dataclass
import re

from expression_preprocess import display_expression, preprocess_for_sympy
from sympy import Add, Mul, collect, expand, simplify, sympify
from sympy.core.expr import Expr
from sympy.core.sympify import SympifyError

SUPPORTED_TOPICS = ("distribution", "foil", "simplification", "linear_steps")

_ALLOWED_CHARS = re.compile(r"^[A-Za-z0-9+\-*/^().\s]+$")
_FUNC_TOKEN = re.compile(r"[A-Za-z]{2,}\s*\(")


class UnsupportedProblemError(ValueError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class SolutionPlan:
    topic: str
    subject: str
    steps: list[str]
    final_answer: str


def _normalize_expr(expr: Expr) -> Expr:
    normalized = expand(expr)
    for sym in normalized.free_symbols:
        normalized = collect(normalized, sym)
    return expand(simplify(normalized))


def _parse_expr(expression: str) -> Expr:
    cleaned = expression.strip()
    if not cleaned:
        raise UnsupportedProblemError("Expression cannot be empty.")
    if "=" in cleaned or ">" in cleaned or "<" in cleaned:
        raise UnsupportedProblemError("Equations and inequalities are not supported in v0.3.")
    if not _ALLOWED_CHARS.match(cleaned):
        raise UnsupportedProblemError(
            "Use keyboard-typable algebra only: letters, digits, + - * / ^ and parentheses."
        )
    if _FUNC_TOKEN.search(cleaned):
        raise UnsupportedProblemError(
            "Function notation (e.g. log, sin, sqrt) is not supported in v0.3."
        )
    if "sqrt" in cleaned.lower():
        raise UnsupportedProblemError("Roots are not supported in v0.3.")

    sympy_ready = preprocess_for_sympy(cleaned)
    try:
        return sympify(sympy_ready, evaluate=False)
    except (SympifyError, TypeError, ValueError) as exc:
        raise UnsupportedProblemError("Expression format is not supported.") from exc


def detect_topic(expression: str) -> str | None:
    expr = _parse_expr(expression)

    if isinstance(expr, Mul):
        add_factors = [arg for arg in expr.args if isinstance(arg, Add)]
        if len(add_factors) >= 3:
            return None
        if len(add_factors) >= 2 and all(len(add.args) == 2 for add in add_factors[:2]):
            return "foil"
        if add_factors:
            return "distribution"

    if isinstance(expr, Add):
        if len(expr.args) >= 2:
            return "linear_steps"
        return "simplification"

    if expr.free_symbols:
        return "simplification"
    return None


def reject_if_unsupported(expression: str) -> None:
    """Raise UnsupportedProblemError when the expression cannot be co-solved in v0.3."""
    _parse_expr(expression)
    if detect_topic(expression) is None:
        raise UnsupportedProblemError(
            "Unsupported problem shape. Supported topics: "
            + ", ".join(SUPPORTED_TOPICS)
            + "."
        )


def build_solution_plan(expression: str) -> SolutionPlan:
    """
    Build a single-hop canonical solution plan for a supported algebra problem.

    Multi-hop paths (e.g. ``2(x+3)+4``) are deferred to Commit 5.
    """
    reject_if_unsupported(expression)
    expr = _parse_expr(expression)
    topic = detect_topic(expression)
    assert topic is not None  # guarded by reject_if_unsupported

    normalized = _normalize_expr(expr)
    final_answer = display_expression(str(normalized))

    return SolutionPlan(
        topic=topic,
        subject="algebra",
        steps=[final_answer],
        final_answer=final_answer,
    )
