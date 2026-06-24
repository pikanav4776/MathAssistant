"""Shared keyboard-math preprocessing for SymPy parsing (^ and ** exponents)."""

from __future__ import annotations

import re

_IMPLICIT_MUL = re.compile(r"(\d+)\*([A-Za-z])")
_PROTECTED_NAMES = ("sqrt", "mod", "pi", "tau", "log", "inv", "finv", "sin", "cos", "tan")
_KNOWN_MATH_IDENTIFIERS = frozenset(
    {"pi", "tau", "sqrt", "mod", "log", "inv", "finv", "sin", "cos", "tan"}
)
_TEXT_ONLY = re.compile(r"^[A-Za-z\s]+$")


def contains_text_like_input(expression: str) -> bool:
    """True when input looks like plain text/words rather than algebra."""
    cleaned = expression.strip()
    if len(cleaned) >= 3 and _TEXT_ONLY.match(cleaned):
        return True
    for match in re.finditer(r"[A-Za-z]+", cleaned):
        token = match.group(0)
        if token == "E":
            continue
        if token.lower() in _KNOWN_MATH_IDENTIFIERS:
            continue
        if len(token) >= 4:
            return True
    return False


def _shield_protected_names(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Prevent implicit-multiplication from splitting known functions/constants."""
    shields: list[tuple[str, str]] = []
    result = text
    for name in _PROTECTED_NAMES:
        pattern = re.compile(re.escape(name), re.IGNORECASE)

        def _replace(_match: re.Match[str], canonical: str = name) -> str:
            token = f"\uE000{len(shields)}\uE001"
            shields.append((token, canonical))
            return token

        result = pattern.sub(_replace, result)
    return result, shields


def _unshield_protected_names(text: str, shields: list[tuple[str, str]]) -> str:
    for token, name in shields:
        text = text.replace(token, name)
    return text


def preprocess_for_sympy(expression: str) -> str:
    """
    Normalize a student-facing algebra string into SymPy-parseable form.

    - Collapses whitespace so ``) (`` becomes implicit multiplication.
    - Accepts ``^`` and ``**`` for exponents (both become ``**`` internally).
    - Inserts implicit multiplication: ``2x``, ``2(x+3)``, ``x(y+1)``, ``)(``.
    """
    compact = re.sub(r"\s+", "", expression.strip())
    compact = re.sub(r"sin\^2\(([^)]+)\)", r"(sin(\1))**2", compact, flags=re.IGNORECASE)
    compact = re.sub(r"cos\^2\(([^)]+)\)", r"(cos(\1))**2", compact, flags=re.IGNORECASE)
    compact = re.sub(r"tan\^2\(([^)]+)\)", r"(tan(\1))**2", compact, flags=re.IGNORECASE)
    compact, shields = _shield_protected_names(compact)

    processed: list[str] = []
    i = 0
    n = len(compact)

    while i < n:
        ch = compact[i]
        nxt = compact[i + 1] if i + 1 < n else ""

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
        elif ch.isalpha() and nxt.isalpha():
            processed.append(ch)
            processed.append("*")
        elif ch == ")" and nxt == "(":
            processed.append(")*")
        else:
            processed.append(ch)
        i += 1

    return _unshield_protected_names("".join(processed), shields)


def display_expression(expr_str: str) -> str:
    """Prefer ``^`` and compact keyboard-style algebra in API-facing strings."""
    cleaned = expr_str.replace("**", "^")
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = re.sub(r"sin\(([^)]+)\)\^2", r"sin^2(\1)", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"cos\(([^)]+)\)\^2", r"cos^2(\1)", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"tan\(([^)]+)\)\^2", r"tan^2(\1)", cleaned, flags=re.IGNORECASE)
    cleaned = _IMPLICIT_MUL.sub(r"\1\2", cleaned)
    cleaned = cleaned.replace("+-", "-")
    cleaned = cleaned.replace("-+", "-")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        inner = cleaned[1:-1]
        if inner.count("(") == inner.count(")"):
            cleaned = inner
    return cleaned
