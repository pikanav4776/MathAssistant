"""Trigonometry-topic solution planning for tutoring sessions."""

from __future__ import annotations

import re
from typing import Any

from sympy import cos, expand, factor, pi, preorder_traversal, simplify, sin, sympify, tan
from sympy.core.expr import Expr
from sympy.core.sympify import SympifyError

from expression_preprocess import display_expression, preprocess_for_sympy
from step_engine import SolutionPlan, UnsupportedProblemError

TRIG_TOPICS = (
    "core_trig",
    "basic_trig_identities",
)

_SYM_LOCALS: dict[str, Any] = {
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "pi": pi,
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
    }
    steps, final_answer = builders[topic](expression)
    if not steps:
        raise UnsupportedProblemError("Could not build steps for this trigonometry problem.")
    return SolutionPlan(topic=topic, subject="trigonometry", steps=steps, final_answer=final_answer)


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
