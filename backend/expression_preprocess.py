"""Shared keyboard-math preprocessing for SymPy parsing (^ and ** exponents)."""

from __future__ import annotations

import re

_IMPLICIT_MUL = re.compile(r"(\d+)\*([A-Za-z])")


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
    """Prefer ``^`` and compact keyboard-style algebra in API-facing strings."""
    cleaned = expr_str.replace("**", "^")
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = _IMPLICIT_MUL.sub(r"\1\2", cleaned)
    cleaned = cleaned.replace("+-", "-")
    cleaned = cleaned.replace("-+", "-")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        inner = cleaned[1:-1]
        if inner.count("(") == inner.count(")"):
            cleaned = inner
    return cleaned
