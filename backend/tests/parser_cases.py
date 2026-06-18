"""
Golden cases for parser() — Phase 1 parsing checklist.

Each row: raw input string and whether parsing should succeed.
Optional ``equivalent_to`` is another expression that must normalize to the same form.
"""

from __future__ import annotations

PARSER_VALID_CASES: list[dict] = [
    {"id": "implicit-digit-letter", "expression": "2x", "equivalent_to": "2*x"},
    {"id": "explicit-mult", "expression": "2*x+3"},
    {"id": "paren-product", "expression": "(x+1)*(x+2)"},
    {"id": "paren-adjacent", "expression": "(x+1)(x+2)", "equivalent_to": "(x+1)*(x+2)"},
    {"id": "caret-exponent", "expression": "x^2"},
    {"id": "python-exponent", "expression": "x**2", "equivalent_to": "x^2"},
    {"id": "nested-exponent", "expression": "(x+1)^2"},
    {"id": "nested-python-exponent", "expression": "(x+1)**2", "equivalent_to": "(x+1)^2"},
    {"id": "distribution-form", "expression": "2*(x+3)"},
    {"id": "multi-variable", "expression": "3*x*y*z"},
    {"id": "negative-coeff", "expression": "-4*a+7*z"},
    {"id": "large-poly", "expression": "x^2+5*x+6"},
]

PARSER_INVALID_CASES: list[dict] = [
    {"id": "division-by-zero", "expression": "1/0", "error_type": "division_by_zero"},
    {"id": "log-zero", "expression": "log(0)", "error_type": "undefined_math"},
    {"id": "consecutive-ops", "expression": "2*/3"},
    {"id": "empty", "expression": ""},
    {"id": "garbage", "expression": "2@3"},
]
