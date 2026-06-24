"""Function-topic solution planning for tutoring sessions."""

from __future__ import annotations

import re
from typing import Any

from sympy import Eq, Mul, Pow, Symbol, expand, log, simplify, solve, sympify
from sympy.core.expr import Expr
from sympy.core.sympify import SympifyError
from sympy.functions.elementary.exponential import log as sympy_log

from expression_preprocess import display_expression, preprocess_for_sympy
from step_engine import SolutionPlan, UnsupportedProblemError

FUNCTION_TOPICS = (
    "function_evaluation",
    "function_composition",
    "inverse_functions",
    "exponential_functions",
    "logarithms",
)

_SYM_LOCALS: dict[str, Any] = {"log": sympy_log}

_DEF_PATTERN = re.compile(r"^([a-zA-Z])\(([a-zA-Z])\)\s*=\s*(.+)$", re.DOTALL)
_CALL_PATTERN = re.compile(r"^([a-zA-Z])\((.+)\)$")
_EXPRESSION_PATTERN = re.compile(r"\d+\^|\(\d+\^")
_LOG_PATTERN = re.compile(r"log\s*\(", re.IGNORECASE)
_INVERSE_TASK_PATTERN = re.compile(
    r"^(?:inv|finv)\([^)]+\)$|^[a-zA-Z]\^-1\([^)]+\)$|^[a-zA-Z]\^\(-1\)\([^)]+\)$",
    re.IGNORECASE,
)


def _is_inverse_task(task: str) -> bool:
    compact = re.sub(r"\s+", "", task.strip())
    return _INVERSE_TASK_PATTERN.match(compact) is not None


def is_function_problem(expression: str) -> bool:
    return detect_function_topic(expression) is not None


def detect_function_topic(expression: str) -> str | None:
    cleaned = expression.strip()
    if not cleaned:
        return None

    if "|" in cleaned:
        defs_part, task_part = cleaned.split("|", 1)
        task = task_part.strip()
        if _is_inverse_task(task):
            return "inverse_functions"
        if _CALL_PATTERN.match(task):
            defs = _parse_definitions(defs_part)
            inner = _CALL_PATTERN.match(task).group(2)  # type: ignore[union-attr]
            if _CALL_PATTERN.match(inner) and len(defs) >= 2:
                return "function_composition"
            if len(defs) >= 1:
                return "function_evaluation"
        return None

    if re.search(r"log\([^,]+,\s*[^)]+\)", cleaned, flags=re.IGNORECASE):
        return "logarithms"
    if _EXPRESSION_PATTERN.search(cleaned):
        return "exponential_functions"
    return None


def try_build_function_plan(expression: str) -> SolutionPlan | None:
    topic = detect_function_topic(expression)
    if topic is None:
        return None

    builders = {
        "function_evaluation": _build_evaluation_plan,
        "function_composition": _build_composition_plan,
        "inverse_functions": _build_inverse_plan,
        "exponential_functions": _build_exponential_plan,
        "logarithms": _build_logarithm_plan,
    }
    steps, final_answer = builders[topic](expression)
    if not steps:
        raise UnsupportedProblemError("Could not build steps for this function problem.")
    return SolutionPlan(topic=topic, subject="algebra", steps=steps, final_answer=final_answer)


def _parse_sympy(expression: str, *, evaluate: bool = True) -> Expr:
    cleaned = preprocess_for_sympy(expression.strip())
    try:
        return sympify(cleaned, locals=_SYM_LOCALS, evaluate=evaluate)
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
        raise UnsupportedProblemError("Expression format is not supported.") from exc


def _split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return [part for part in parts if part]


def _parse_definitions(defs_part: str) -> dict[str, tuple[str, str]]:
    definitions: dict[str, tuple[str, str]] = {}
    for piece in _split_top_level_commas(defs_part):
        match = _DEF_PATTERN.match(piece.strip())
        if not match:
            raise UnsupportedProblemError(f"Invalid function definition: {piece}")
        name, variable, body = match.groups()
        definitions[name] = (variable, body.strip())
    if not definitions:
        raise UnsupportedProblemError("Function problems require at least one definition.")
    return definitions


def _display(expr: Expr | str) -> str:
    if isinstance(expr, Expr):
        return display_expression(str(expr))
    return display_expression(str(expr))


def _evaluate_call(
    call_name: str,
    argument: Expr,
    arg_text: str,
    definitions: dict[str, tuple[str, str]],
) -> tuple[list[str], Expr]:
    if call_name not in definitions:
        raise UnsupportedProblemError(f"Unknown function: {call_name}")
    variable, body = definitions[call_name]
    var_symbol = Symbol(variable)
    body_expr = _parse_sympy(body)
    arg_display = _display(argument)
    substituted_display = _substitute_in_body(body, variable, arg_text)
    result = simplify(body_expr.subs(var_symbol, argument))
    final_display = _display(result)
    steps = [f"{call_name}({arg_display})={substituted_display}"]
    if final_display != substituted_display:
        steps.append(final_display)
    return steps, result


def _substitute_in_body(body: str, variable: str, argument: str) -> str:
    arg_clean = argument.strip()
    if arg_clean.startswith("(") and arg_clean.endswith(")"):
        inner = arg_clean[1:-1]
        if inner.replace(".", "").replace("-", "").isdigit():
            arg_clean = inner
    replaced = re.sub(rf"(?<=\d){re.escape(variable)}(?!\w)", f"({arg_clean})", body)
    replaced = re.sub(rf"^{re.escape(variable)}(?!\w)", f"({arg_clean})", replaced)
    replaced = re.sub(rf"(?<=[+\-*/(,\|]){re.escape(variable)}(?!\w)", f"({arg_clean})", replaced)
    if replaced == body:
        replaced = body.replace(variable, arg_clean if arg_clean.isdigit() or arg_clean.replace("-", "").isdigit() else f"({arg_clean})")
    return display_expression(replaced)


def _parse_call(task: str) -> tuple[str, str]:
    match = _CALL_PATTERN.match(task.strip())
    if not match:
        raise UnsupportedProblemError(f"Invalid function call: {task}")
    return match.group(1), match.group(2)


def _build_evaluation_plan(expression: str) -> tuple[list[str], str]:
    defs_part, task_part = expression.split("|", 1)
    definitions = _parse_definitions(defs_part)
    steps, result = _resolve_call_expression(task_part, definitions)
    return steps, _display(result)


def _build_composition_plan(expression: str) -> tuple[list[str], str]:
    defs_part, task_part = expression.split("|", 1)
    definitions = _parse_definitions(defs_part)
    steps, result = _resolve_call_expression(task_part, definitions)
    return steps, _display(result)


def _resolve_call_expression(
    task: str,
    definitions: dict[str, tuple[str, str]],
) -> tuple[list[str], Expr]:
    call_name, arg_text = _parse_call(task)
    arg_steps: list[str] = []
    if _CALL_PATTERN.match(arg_text.strip()):
        inner_name, _ = _parse_call(arg_text.strip())
        if inner_name in definitions:
            arg_steps, arg_value = _resolve_call_expression(arg_text.strip(), definitions)
            arg_text_display = _display(arg_value)
        else:
            arg_value = _parse_sympy(arg_text)
            arg_text_display = arg_text
    else:
        arg_value = _parse_sympy(arg_text)
        arg_text_display = arg_text

    steps, result = _evaluate_call(call_name, arg_value, arg_text_display, definitions)
    return arg_steps + steps, result


def _build_inverse_plan(expression: str) -> tuple[list[str], str]:
    defs_part, _task_part = expression.split("|", 1)
    definitions = _parse_definitions(defs_part)
    if len(definitions) != 1:
        raise UnsupportedProblemError("Inverse problems require exactly one function definition.")

    function_name, (variable, body) = next(iter(definitions.items()))
    var_symbol = Symbol(variable)
    y_symbol = Symbol("y")
    body_expr = _parse_sympy(body)

    equation = Eq(y_symbol, body_expr)
    solutions = solve(equation, var_symbol)
    if len(solutions) != 1:
        raise UnsupportedProblemError("Inverse is only supported for one-to-one linear functions.")

    inverse_expr = solutions[0].subs(var_symbol, y_symbol).subs(y_symbol, var_symbol)
    inverse_expr = simplify(inverse_expr)

    steps = [
        f"y={_display(body_expr)}",
        f"{variable}={_display(solutions[0])}",
        _display(inverse_expr),
    ]
    return steps, _display(inverse_expr)


def _build_exponential_plan(expression: str) -> tuple[list[str], str]:
    cleaned = expression.strip()
    manual = _manual_exponential_steps(cleaned)
    if manual is not None:
        return manual

    expr = _parse_sympy(cleaned, evaluate=False)
    simplified = simplify(expr)
    final_display = _display(simplified)
    return [final_display], final_display


def _manual_exponential_steps(expression: str) -> tuple[list[str], str] | None:
    nested = re.match(r"^\((\d+)\^(\d+)\)\^(\d+)$", expression.replace(" ", ""))
    if nested:
        base, inner_exp, outer_exp = nested.groups()
        combined_exp = int(inner_exp) * int(outer_exp)
        combined = f"{base}^{combined_exp}"
        final_value = int(base) ** combined_exp
        return [combined, str(final_value)], str(final_value)

    if "*" in expression:
        powers = re.findall(r"(\d+)\^(\d+)", expression.replace(" ", ""))
        if len(powers) >= 2:
            bases = {base for base, _ in powers}
            if len(bases) == 1:
                base = next(iter(bases))
                exponent_sum = sum(int(exp) for _, exp in powers)
                combined = f"{base}^{exponent_sum}"
                final_value = int(base) ** exponent_sum
                return [combined, str(final_value)], str(final_value)

    division = re.match(r"^(\d+)\^(\d+)/(\d+)\^(\d+)$", expression.replace(" ", ""))
    if division:
        base, num_exp, same_base, den_exp = division.groups()
        if base == same_base:
            combined_exp = int(num_exp) - int(den_exp)
            combined = f"{base}^{combined_exp}"
            final_value = int(base) ** combined_exp
            return [combined, str(final_value)], str(final_value)

    power_times_base = re.match(r"^(\d+)\^(\d+)\*(\d+)$", expression.replace(" ", ""))
    if power_times_base:
        base, exp, multiplier = power_times_base.groups()
        if base == multiplier:
            combined_exp = int(exp) + 1
            combined = f"{base}^{combined_exp}"
            final_value = int(base) ** combined_exp
            return [combined, str(final_value)], str(final_value)
    return None


def _combine_numeric_powers(expr: Expr) -> tuple[str, Expr] | None:
    if isinstance(expr, Mul):
        pows = [arg for arg in expr.args if isinstance(arg, Pow)]
        if len(pows) >= 2:
            bases = {pow_arg.base for pow_arg in pows}
            if len(bases) == 1:
                base = next(iter(bases))
                exponent_sum = sum(pow_arg.exp for pow_arg in pows)
                other_factors = [arg for arg in expr.args if not isinstance(arg, Pow)]
                combined = Pow(base, exponent_sum)
                for factor in other_factors:
                    combined *= factor
                combined = simplify(combined)
                return _display(Pow(base, exponent_sum)), combined

    if isinstance(expr, Pow) and isinstance(expr.base, Pow):
        inner_base = expr.base.base
        inner_exp = expr.base.exp
        outer_exp = expr.exp
        combined = Pow(inner_base, inner_exp * outer_exp)
        simplified = simplify(combined)
        return _display(combined), simplified

    if isinstance(expr, Pow):
        simplified = simplify(expr)
        if simplified != expr:
            return _display(expr), simplified
    return None


def _build_logarithm_plan(expression: str) -> tuple[list[str], str]:
    cleaned = expression.strip()
    manual = _manual_log_steps(cleaned)
    if manual is not None:
        return manual

    expr = _parse_sympy(cleaned)
    simplified = simplify(expr)
    final_display = _display(simplified)
    return [final_display], final_display


def _manual_log_steps(expression: str) -> tuple[list[str], str] | None:
    compact = expression.replace(" ", "")
    terms = re.findall(r"log\((\d+),(\d+)\)", compact, flags=re.IGNORECASE)
    if len(terms) >= 2 and "+" in compact:
        bases = {base for _, base in terms}
        if len(bases) == 1:
            base = next(iter(bases))
            product = 1
            for value, _ in terms:
                product *= int(value)
            combined = f"log({product},{base})"
            final_value = simplify(_parse_sympy(combined))
            return [combined, _display(final_value)], _display(final_value)

    if len(terms) == 2 and "-" in compact:
        bases = {base for _, base in terms}
        if len(bases) == 1:
            base = next(iter(bases))
            left, right = terms
            quotient = int(left[0]) // int(right[0])
            combined = f"log({quotient},{base})"
            final_value = simplify(_parse_sympy(combined))
            return [combined, _display(final_value)], _display(final_value)

    if len(terms) == 2 and "/" in compact:
        bases = {base for _, base in terms}
        if len(bases) == 1:
            left, right = terms
            left_value = simplify(_parse_sympy(f"log({left[0]},{left[1]})"))
            right_value = simplify(_parse_sympy(f"log({right[0]},{right[1]})"))
            if right_value == 0:
                return None
            quotient = simplify(left_value / right_value)
            return [compact, _display(quotient)], _display(quotient)
    return None


def _combine_logs(expr: Expr) -> tuple[str, Expr] | None:
    from sympy import logcombine

    combined = logcombine(expr, force=True)
    if combined != expr:
        simplified = simplify(combined)
        if simplified != expr:
            return _display(combined), simplified
    return None
