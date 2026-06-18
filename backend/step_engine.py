from __future__ import annotations

from dataclasses import dataclass
import re

from sympy import Add, Mul, collect, expand, simplify, sympify
from sympy.core.expr import Expr
from sympy.core.sympify import SympifyError


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


_ALLOWED_CHARS = re.compile(r"^[A-Za-z0-9+\-*/^().\s]+$")
_FUNC_TOKEN = re.compile(r"[A-Za-z]{2,}\s*\(")


def _normalize_expr(expr: Expr) -> Expr:
    normalized = expand(expr)
    for sym in normalized.free_symbols:
        normalized = collect(normalized, sym)
    return expand(simplify(normalized))


def _parse_expr(expression: str) -> Expr:
    cleaned = expression.strip()
    if not cleaned:
        raise UnsupportedProblemError("Expression cannot be empty.")
    if not _ALLOWED_CHARS.match(cleaned):
        raise UnsupportedProblemError(
            "Use keyboard-typable algebra only: letters, digits, + - * / ^ and parentheses."
        )
    if "=" in cleaned or ">" in cleaned or "<" in cleaned:
        raise UnsupportedProblemError("Equations and inequalities are not supported in v0.3.")
    if _FUNC_TOKEN.search(cleaned):
        raise UnsupportedProblemError("Function notation (e.g. log, sin, sqrt) is not supported in v0.3.")
    if "sqrt" in cleaned.lower():
        raise UnsupportedProblemError("Roots are not supported in v0.3.")
    processed: list[str] = []
    for idx, ch in enumerate(cleaned):
        nxt = cleaned[idx + 1] if idx + 1 < len(cleaned) else ""
        if ch == "^":
            processed.append("**")
        elif ch.isdigit() and nxt.isalpha():
            processed.append(ch)
            processed.append("*")
        elif ch.isdigit() and nxt == "(":
            processed.append(ch)
            processed.append("*")
        elif ch.isalpha() and nxt == "(":
            processed.append(ch)
            processed.append("*")
        elif ch == ")" and nxt == "(":
            processed.append(")*")
        else:
            processed.append(ch)
    cleaned = "".join(processed)

    try:
        return sympify(cleaned, evaluate=False)
    except (SympifyError, TypeError, ValueError) as exc:
        raise UnsupportedProblemError("Expression format is not supported.") from exc


def detect_topic(expression: str) -> str | None:
    expr = _parse_expr(expression)

    if isinstance(expr, Mul):
        add_factors = [arg for arg in expr.args if isinstance(arg, Add)]
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


def build_solution_plan(expression: str) -> SolutionPlan:
    expr = _parse_expr(expression)
    topic = detect_topic(expression)
    if topic is None:
        raise UnsupportedProblemError(
            "Unsupported problem shape. Supported topics: distribution, foil, simplification, linear_steps."
        )

    # Optional multi-hop paths for mixed expressions (e.g. 2(x+3)+4):
    # first expand multiplicative block(s), then combine like terms.
    steps: list[str] = []
    if isinstance(expr, Add):
        expanded_terms = []
        changed = False
        for term in expr.args:
            if isinstance(term, Mul) and any(isinstance(arg, Add) for arg in term.args):
                expanded_term = expand(term)
                expanded_terms.append(expanded_term)
                changed = True
            else:
                expanded_terms.append(term)
        if changed:
            intermediate = Add(*expanded_terms, evaluate=False)
            intermediate_str = str(intermediate).replace("**", "^")
            steps.append(intermediate_str)
            normalized = _normalize_expr(intermediate)
            final_answer = str(normalized).replace("**", "^")
            if final_answer != intermediate_str:
                steps.append(final_answer)
            else:
                steps = [final_answer]
        else:
            normalized = _normalize_expr(expr)
            final_answer = str(normalized).replace("**", "^")
            steps = [final_answer]
    else:
        normalized = _normalize_expr(expr)
        final_answer = str(normalized).replace("**", "^")
        steps = [final_answer]

    return SolutionPlan(
        topic=topic,
        subject="algebra",
        steps=steps,
        final_answer=final_answer,
    )
