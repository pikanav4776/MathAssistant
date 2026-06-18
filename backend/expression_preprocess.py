"""Shared keyboard-math preprocessing for SymPy parsing (^ and ** exponents)."""

from __future__ import annotations


def preprocess_for_sympy(expression: str) -> str:
    """
    Normalize a student-facing algebra string into SymPy-parseable form.

    - Accepts ``^`` and ``**`` for exponents (both become ``**`` internally).
    - Inserts implicit multiplication: ``2x``, ``2(x+3)``, ``x(y+1)``, ``)(``.
    """
    processed: list[str] = []
    i = 0
    n = len(expression)

    while i < n:
        ch = expression[i]
        nxt = expression[i + 1] if i + 1 < n else ""

        if ch == "*" and nxt == "*":
            processed.append("**")
            i += 2
            continue
        if ch == "^":
            processed.append("**")
        elif ch.isdigit() and (nxt.isalpha() or nxt == "("):
            processed.append(ch)
            processed.append("*")
        elif ch.isalpha() and nxt == "(":
            processed.append(ch)
            processed.append("*")
        elif ch == ")" and nxt == "(":
            processed.append(")*")
        else:
            processed.append(ch)
        i += 1

    return "".join(processed)


def display_expression(expr_str: str) -> str:
    """Prefer ``^`` in API-facing expression strings."""
    return expr_str.replace("**", "^")
