"""Trigonometry-topic solution planning for tutoring sessions."""

from __future__ import annotations

import re
from typing import Any

from sympy import cos, expand, factor, pi, preorder_traversal, simplify, sin, solve, sqrt, sympify, tan
from sympy import Eq, S, Add, Mul, Symbol
from sympy.core.expr import Expr
from sympy.core.sympify import SympifyError

from expression_preprocess import display_expression, preprocess_for_sympy
from step_engine import SolutionPlan, UnsupportedProblemError

TRIG_TOPICS = (
    "core_trig",
    "basic_trig_identities",
    "trig_equations",
)

_SYM_LOCALS: dict[str, Any] = {
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "pi": pi,
    "sqrt": sqrt,
}

_TRIG_PATTERN = re.compile(
    r"(?:sin|cos|tan)(?:\^2)?\s*\(",
    re.IGNORECASE,
)
_IDENTITY_SIN2_PATTERN = re.compile(
    r"sin\^2\([^)]+\)|sin\([^)]+\)\^2",
    re.IGNORECASE,
)
_IDENTITY_COS2_PATTERN = re.compile(
    r"cos\^2\([^)]+\)|cos\([^)]+\)\^2",
    re.IGNORECASE,
)


def is_trig_problem(expression: str) -> bool:
    return detect_trig_topic(expression) is not None


def detect_trig_topic(expression: str) -> str | None:
    cleaned = expression.strip()
    if not cleaned or not _TRIG_PATTERN.search(cleaned):
        return None
    if _is_trig_equation(cleaned):
        return "trig_equations"
    if _is_identity_expression(cleaned):
        return "basic_trig_identities"
    return "core_trig"


def try_build_trig_plan(expression: str) -> SolutionPlan | None:
    topic = detect_trig_topic(expression)
    if topic is None:
        return None

    builders = {
        "core_trig": _build_core_trig_plan,
        "basic_trig_identities": _build_identity_plan,
        "trig_equations": _build_trig_equation_plan,
    }
    steps, final_answer = builders[topic](expression)
    if not steps:
        raise UnsupportedProblemError("Could not build steps for this trigonometry problem.")
    return SolutionPlan(topic=topic, subject="trigonometry", steps=steps, final_answer=final_answer)


def _is_trig_equation(expression: str) -> bool:
    compact = re.sub(r"\s+", "", expression)
    if any(op in compact for op in ("<=", ">=", "==", "!=", "<", ">")):
        return False
    if compact.count("=") != 1:
        return False
    return True


def _is_identity_expression(expression: str) -> bool:
    compact = re.sub(r"\s+", "", expression)
    return (
        _IDENTITY_SIN2_PATTERN.search(compact) is not None
        and _IDENTITY_COS2_PATTERN.search(compact) is not None
    )


def _parse_trig_sympy(expression: str, *, evaluate: bool = True) -> Expr:
    cleaned = preprocess_for_sympy(expression.strip())
    try:
        return sympify(cleaned, locals=_SYM_LOCALS, evaluate=evaluate)
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        raise UnsupportedProblemError("Expression format is not supported.") from exc


def _display(expr: Expr | str) -> str:
    if isinstance(expr, Expr):
        return display_expression(str(expr))
    return display_expression(str(expr))


def _collect_trig_angles(expr: Expr) -> set[Expr]:
    angles: set[Expr] = set()
    for node in preorder_traversal(expr):
        if getattr(node, "func", None) in (sin, cos, tan) and node.args:
            angles.add(node.args[0])
    return angles


def _is_trig_call(node: Expr) -> bool:
    return getattr(node, "func", None) in (sin, cos, tan)


def _contains_identity_pair(expr: Expr) -> bool:
    for theta in _collect_trig_angles(expr):
        pair = sin(theta) ** 2 + cos(theta) ** 2
        if expr.has(pair):
            return True
    return False


def _evaluate_remaining_trig(working: Expr) -> tuple[list[str], Expr]:
    steps: list[str] = []
    while True:
        replacements: list[tuple[Expr, Expr]] = []
        for node in preorder_traversal(working):
            if not _is_trig_call(node):
                continue
            evaluated = simplify(node)
            if evaluated != node:
                replacements.append((node, evaluated))
        if not replacements:
            break

        target, value = replacements[0]
        for candidate, candidate_value in replacements:
            if not any(
                candidate != other and candidate.has(other)
                for other, _ in replacements
            ):
                target, value = candidate, candidate_value
                break

        working = working.xreplace({target: value})
        step_display = _display(working)
        if not steps or steps[-1] != step_display:
            steps.append(step_display)
    return steps, working


def _build_core_trig_plan(expression: str) -> tuple[list[str], str]:
    expr = _parse_trig_sympy(expression, evaluate=False)
    final = simplify(expr)
    final_display = _display(final)

    if expr == final:
        return [final_display], final_display

    steps, working = _evaluate_remaining_trig(expr)
    if not steps:
        return [final_display], final_display
    if steps[-1] != final_display:
        steps.append(final_display)
    return steps, final_display


def _substitute_pythagorean(expr: Expr) -> tuple[Expr, bool]:
    angles = sorted(_collect_trig_angles(expr), key=str)
    for candidate in (expr, factor(expr), expand(expr)):
        for theta in angles:
            pair = sin(theta) ** 2 + cos(theta) ** 2
            matches = list(candidate.find(pair))
            if not matches:
                continue
            replacement = candidate.xreplace({matches[0]: 1})
            if replacement != candidate:
                return replacement, True
    return expr, False


def _build_identity_plan(expression: str) -> tuple[list[str], str]:
    expr = _parse_trig_sympy(expression, evaluate=False)
    steps: list[str] = []
    working = expr
    original_display = _display(working)

    for _ in range(6):
        progressed = False

        factored = factor(working)
        if factored != working and _contains_identity_pair(factored):
            factored_display = _display(factored)
            if not steps:
                steps.append(original_display)
            if steps[-1] != factored_display:
                steps.append(factored_display)
            working = factored
            progressed = True

        rewritten, changed = _substitute_pythagorean(working)
        if changed:
            rewritten_display = _display(rewritten)
            if not steps:
                steps.append(original_display)
            if steps[-1] != rewritten_display:
                steps.append(rewritten_display)
            working = rewritten
            progressed = True

        if not progressed:
            break

    eval_steps, working = _evaluate_remaining_trig(working)
    if eval_steps:
        if not steps:
            steps.append(original_display)
        for step in eval_steps:
            if not steps or steps[-1] != step:
                steps.append(step)

    final = simplify(working)
    final_display = _display(final)
    if not steps:
        return [final_display], final_display
    if steps[-1] != final_display:
        steps.append(final_display)
    return steps, final_display


def _eq_display(lhs: Expr, rhs: Expr) -> str:
    return f"{_display(lhs)}={_display(rhs)}"


def _equation_variable(lhs: Expr, rhs: Expr) -> Symbol:
    symbols = sorted((lhs - rhs).free_symbols, key=lambda symbol: str(symbol).lower())
    if len(symbols) != 1:
        raise UnsupportedProblemError("Trig equations must have exactly one unknown.")
    symbol = symbols[0]
    if not isinstance(symbol, Symbol):
        raise UnsupportedProblemError("Trig equations must solve for a single variable.")
    return symbol


def _contains_trig_of_var(expr: Expr, var: Symbol) -> bool:
    for node in preorder_traversal(expr):
        if _is_trig_call(node) and node.args and node.args[0] == var:
            return True
    return False


def _split_coeff_trig(expr: Expr, var: Symbol) -> tuple[Expr, Expr] | None:
    if _is_trig_call(expr) and expr.args[0] == var:
        return S.One, expr
    if isinstance(expr, Mul):
        coeff = S.One
        trig: Expr | None = None
        for arg in expr.args:
            if _is_trig_call(arg) and arg.args[0] == var:
                if trig is not None:
                    return None
                trig = arg
            elif not arg.free_symbols:
                coeff *= arg
            else:
                return None
        if trig is not None:
            return simplify(coeff), trig
    return None


def _isolate_trig_equation_steps(
    lhs: Expr,
    rhs: Expr,
    var: Symbol,
) -> list[tuple[Expr, Expr]]:
    steps: list[tuple[Expr, Expr]] = []
    working_lhs, working_rhs = expand(lhs), expand(rhs)

    balanced = _try_balance_opposing_trig_terms(working_lhs, working_rhs, var)
    if balanced is not None:
        steps.append(balanced)
        return steps

    if isinstance(working_lhs, Add) and _contains_trig_of_var(working_lhs, var):
        const_part = S.Zero
        trig_coeff: Expr | None = None
        trig_call: Expr | None = None
        for term in working_lhs.args:
            split = _split_coeff_trig(term, var)
            if split is not None:
                coeff, trig = split
                if trig_call is not None:
                    raise UnsupportedProblemError(
                        "Trig equations with multiple trig terms are not supported."
                    )
                trig_coeff = coeff
                trig_call = trig
            else:
                const_part += term
        if trig_call is not None and const_part != S.Zero:
            working_lhs = trig_coeff * trig_call  # type: ignore[operator]
            working_rhs = simplify(working_rhs - const_part)
            steps.append((working_lhs, working_rhs))
            lhs, rhs = working_lhs, working_rhs

    split = _split_coeff_trig(lhs, var)
    if split is not None:
        coeff, trig = split
        if coeff != S.One:
            isolated_rhs = simplify(rhs / coeff)
            steps.append((trig, isolated_rhs))
    return steps


def _try_balance_opposing_trig_terms(
    lhs: Expr,
    rhs: Expr,
    var: Symbol,
) -> tuple[Expr, Expr] | None:
    if rhs != S.Zero or not isinstance(lhs, Add):
        return None

    trig_terms: list[Expr] = []
    const_part = S.Zero
    for term in lhs.args:
        if _contains_trig_of_var(term, var):
            trig_terms.append(term)
        else:
            const_part += term
    if const_part != S.Zero or len(trig_terms) != 2:
        return None

    left_trig, right_trig = trig_terms[0], -trig_terms[1]
    return left_trig, right_trig


def _solution_sort_key(solution: Expr) -> float:
    from sympy import N

    try:
        return float(N(simplify(solution)))
    except (TypeError, ValueError):
        return float("inf")


def _format_variable_solutions(var: Symbol, solutions: list[Expr]) -> str:
    var_name = str(var)
    ordered = sorted(solutions, key=_solution_sort_key)
    rendered = [f"{var_name}={_display(simplify(solution))}" for solution in ordered]
    return ",".join(rendered)


def _build_trig_equation_plan(expression: str) -> tuple[list[str], str]:
    lhs_text, rhs_text = expression.split("=", 1)
    if not lhs_text.strip() or not rhs_text.strip():
        raise UnsupportedProblemError("Trig equations require both sides around =.")

    lhs = _parse_trig_sympy(lhs_text, evaluate=False)
    rhs = _parse_trig_sympy(rhs_text, evaluate=False)
    var = _equation_variable(lhs, rhs)

    steps = [_eq_display(lhs, rhs)]
    for iso_lhs, iso_rhs in _isolate_trig_equation_steps(lhs, rhs, var):
        iso_step = _eq_display(iso_lhs, iso_rhs)
        if iso_step != steps[-1]:
            steps.append(iso_step)
        lhs, rhs = iso_lhs, iso_rhs

    solutions = solve(Eq(lhs, rhs), var)
    if not solutions:
        raise UnsupportedProblemError("No solution found for this trig equation.")

    final = _format_variable_solutions(var, solutions)
    if steps[-1] != final:
        steps.append(final)
    return steps, final
