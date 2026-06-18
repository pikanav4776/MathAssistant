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


def _flatten_add_terms(expr: Add) -> list[Expr]:
    parts: list[Expr] = []
    for arg in expr.args:
        expanded = expand(arg)
        if isinstance(expanded, Add):
            parts.extend(expanded.args)
        else:
            parts.append(expanded)
    return parts


def _term_display(term: Expr) -> str:
    return display_expression(str(expand(term)))


def _ordered_add_display(expanded_terms: list[Expr]) -> str:
    var_parts: list[str] = []
    const_parts: list[str] = []
    for term in expanded_terms:
        inner = expand(term)
        parts = list(inner.args) if isinstance(inner, Add) else [inner]
        for part in parts:
            rendered = _term_display(part)
            if part.free_symbols:
                var_parts.append(rendered)
            else:
                const_parts.append(rendered)
    rendered_all = var_parts + const_parts
    if not rendered_all:
        return ""
    result = rendered_all[0]
    for piece in rendered_all[1:]:
        if piece.startswith("-"):
            result += piece
        else:
            result += f"+{piece}"
    return result


def _student_display(expr: Expr) -> str:
    if isinstance(expr, Add):
        expr = Add(*_flatten_add_terms(expr), evaluate=False)
    return display_expression(str(expr))


def canonical_step_display(expression: str) -> str:
    """Normalize an expression to its keyboard-style canonical step string."""
    expr = _parse_expr(expression)
    if isinstance(expr, Add):
        return _ordered_add_display(list(expr.args))
    return _student_display(expr)


def _build_multihop_steps(expr: Add) -> list[str] | None:
    """
    Expand distributive/foil blocks inside a sum, then combine like terms.

    Returns intermediate canonical steps when the expanded form differs from
    the fully simplified answer (e.g. ``2(x+3)+4`` → ``2x+6+4``, ``2x+10``).
    """
    expanded_terms: list[Expr] = []
    changed = False
    for term in expr.args:
        if isinstance(term, Mul) and any(isinstance(arg, Add) for arg in term.args):
            expanded_terms.append(expand(term))
            changed = True
        else:
            expanded_terms.append(term)
    if not changed:
        return None

    intermediate = Add(*expanded_terms, evaluate=False)
    intermediate_str = _ordered_add_display(expanded_terms)
    normalized = _normalize_expr(intermediate)
    final_answer = _student_display(normalized)
    if final_answer == intermediate_str:
        return [final_answer]
    return [intermediate_str, final_answer]


def build_solution_plan(expression: str) -> SolutionPlan:
    """Build a canonical solution plan (single- or multi-hop) for a supported problem."""
    reject_if_unsupported(expression)
    expr = _parse_expr(expression)
    topic = detect_topic(expression)
    assert topic is not None  # guarded by reject_if_unsupported

    steps: list[str]
    if isinstance(expr, Add):
        multihop = _build_multihop_steps(expr)
        if multihop is not None:
            steps = multihop
        else:
            normalized = _normalize_expr(expr)
            steps = [_student_display(normalized)]
    else:
        normalized = _normalize_expr(expr)
        steps = [_student_display(normalized)]

    final_answer = steps[-1]
    return SolutionPlan(
        topic=topic,
        subject="algebra",
        steps=steps,
        final_answer=final_answer,
    )
