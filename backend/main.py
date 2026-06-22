"""
MathAssistant â€“ FastAPI + SymPy tutoring backend
=================================================
Data flow (one request):

  raw student string  (^ or ** for exponents, e.g. x^2 or x**2)
       â”‚
       â–¼
  [PARSING LAYER]        parser()              pre-process & sympify
       â”‚
       â–¼
  [NORMALIZATION LAYER]  normalize()           expand â†’ collect â†’ simplify
       â”‚
       â–¼
  [COMPARISON LAYER]     comparison()          equivalence check + structural diff
       â”‚
       â–¼
  [CLASSIFICATION LAYER] classify_error()      deterministic rule-based error taxonomy
       â”‚
       â–¼
  [HINT ENGINE]          generate_hint()       error_type â†’ hint string
       â”‚
       â–¼
  JSON response

Note: solve(), integrate(), and diff() are not used on the MVP validation path.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
from typing import Callable, TypeVar

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession 
from pydantic import BaseModel
from sympy import (
    Add, E, Mod, Mul, Pow,
    expand, collect, simplify, sympify, sqrt,
    zoo, nan, oo, pi as Pi,
)
from sympy.core.expr import Expr
from sympy.core.relational import Relational
from sympy.core.sympify import SympifyError

from db.database import check_db_connection, get_db, init_db
from auth.deps import get_optional_user, require_admin
from auth.routes import router as auth_router
from session_access import assert_session_access
from session_detail import step_index_for_session
from session_routes import router as session_router
from db.models import Attempt, Problem, SolutionPath, SolutionStep, TutoringSession, User, UserRole
from expression_preprocess import preprocess_for_sympy, contains_text_like_input
from step_engine import (
    UnsupportedProblemError,
    build_solution_plan,
    canonical_step_display,
    is_factor_reorder_submission,
)

logger = logging.getLogger(__name__)


def _init_sentry() -> None:
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    traces_rate_raw = os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1").strip()
    try:
        traces_sample_rate = float(traces_rate_raw)
    except ValueError:
        traces_sample_rate = 0.1

    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        traces_sample_rate=traces_sample_rate,
    )


_init_sentry()

T = TypeVar("T") 
_EXECUTOR = ThreadPoolExecutor(max_workers=2) 
_NORMALIZE_TIMEOUT_SEC = 10.0 

MAX_ATTEMPTS_BEFORE_ESCALATION = 3
MAX_ATTEMPTS_BEFORE_REVEAL = 5

_SYMPY_LOCALS = {
    "e": E,
    "E": E,
    "pi": Pi,
    "tau": 2 * Pi,
    "mod": Mod,
    "sqrt": sqrt,
}


def _align_student_symbols_to_reference(student_expr: Expr, reference_expr: Expr) -> Expr:
    """Map student variable symbols to reference casing when names differ only by case."""
    ref_by_lower = {str(symbol).lower(): symbol for symbol in reference_expr.free_symbols}
    substitutions = {}
    for student_symbol in student_expr.free_symbols:
        canonical = ref_by_lower.get(str(student_symbol).lower())
        if canonical is not None and student_symbol != canonical:
            substitutions[student_symbol] = canonical
    if substitutions:
        return student_expr.subs(substitutions)
    return student_expr

# Pre-parse guards (before SymPy evaluates)
_DIV_ZERO_PATTERN = re.compile(
    r"/\s*0(?:\s*[^0-9.]|\s*$)|"
    r"(?:^|[+\-*/(])\s*0\s*/\s*(?:[^0-9.]|$)"
)
_UNDEFINED_TEXT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"log\s*\(\s*0\s*\)", re.I), "logarithm of zero is undefined"),
    (re.compile(r"0\s*\^\s*0\b"), "0^0 is indeterminate"),
    (re.compile(r"oo\s*-\s*oo", re.I), "infinity minus infinity is undefined"),
]

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# App bootstrap
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MathAssistant", version="1.0.0", lifespan=lifespan)

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        return _DEFAULT_CORS_ORIGINS
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.include_router(auth_router)
app.include_router(session_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _assert_session_access(session_row: TutoringSession, user: User | None) -> None:
    assert_session_access(session_row, user)

# Request / response models
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class StepInput(BaseModel):
    session_id: str
    step: str
    expected: str | None = None


class SkippedStepInfo(BaseModel):
    step_order: int
    expected: str


class StepResult(BaseModel):
    session_id: str
    received_step: str
    expected_step: str
    is_equivalent: bool
    structural_diff: dict | None
    error_classification: dict | None
    hint: str
    step_index: int | None = None
    step_count: int | None = None
    is_final_step: bool | None = None
    session_complete: bool | None = None
    current_expression: str | None = None
    skipped_steps: list[SkippedStepInfo] | None = None
    skip_message: str | None = None


class StartSessionRequest(BaseModel):
    problem_id: str | None = None
    problem_expression: str | None = None
    expected_final: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    problem_id: str
    problem_expression: str
    expected_final: str
    message: str
    subject: str | None = None
    topic: str | None = None
    current_expression: str | None = None
    step_count: int | None = None


class ProblemResponse(BaseModel):
    id: str
    expression: str
    expected_final: str
    difficulty: str | None
    topic: str | None
    created_at: datetime


class ProblemCreateRequest(BaseModel): # this is the request body for creating a problem
    id: str
    expression: str
    expected_final: str
    difficulty: str | None = None
    topic: str | None = None


class SessionSummary(BaseModel):
    session_id: str
    problem_id: str
    problem_expression: str
    attempt_count: int
    hint_level: int
    completed: bool | None = None
    current_expression: str | None = None
    attempt_history: list[dict]
    created_at: datetime
    last_active: datetime
    expected_final: str | None = None
    topic: str | None = None
    step_index: int = 1
    step_count: int = 1
    incorrect_attempt_count: int = 0


@dataclass
class SessionState:
    session_id: str
    problem_id: str
    problem_expression: str
    expected_final: str
    attempt_count: int = 0
    incorrect_attempt_count: int = 0
    attempt_history: list[dict] = field(default_factory=list)
    hint_level: int = 1
    created_at: datetime = field(default_factory=_utc_now)
    last_active: datetime = field(default_factory=_utc_now)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Input / engine exceptions (never expose raw SymPy messages to students)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class MathInputError(ValueError):
    """Base for user-input problems detected before or during parsing."""

    category = "invalid_input"
    user_message = "That expression could not be read. Check your notation."

    def __init__(self, message: str, *, user_message: str | None = None):
        super().__init__(message)
        if user_message is not None:
            self.user_message = user_message


class ParseError(MathInputError):
    """Legacy alias â€” malformed or unsupported input."""

    category = "malformed_syntax"


class InvalidFormatError(ParseError):
    """Correct domain but wrong notation (e.g. ** instead of ^)."""

    category = "invalid_format"


class MalformedSyntaxError(ParseError):
    """Syntactically broken input."""

    category = "malformed_syntax"
    user_message = "Check operators and parentheses â€” something in the syntax is invalid."


class DivisionByZeroError(ParseError):
    """Division by zero in a literal sub-expression."""

    category = "division_by_zero"
    user_message = "Division by zero is not defined. Check denominators in your step."


class UndefinedMathError(ParseError):
    """Valid syntax but mathematically undefined result."""

    category = "undefined_math"
    user_message = "That expression is not defined for the values used (e.g. log(0))."


class UndefinedSymbolError(ParseError):
    """Unrecognized identifier or function name."""

    category = "undefined_symbol"
    user_message = "An unknown symbol or function was used. Use only variables from the problem."


class EvaluationTimeoutError(ParseError):
    """expand/simplify exceeded the complexity guard."""

    category = "evaluation_timeout"
    user_message = "This expression is too complex to check quickly. Try a simpler form."


class EngineError(Exception):
    """Unexpected internal failure â€” logged, generic message to client."""

    category = "engine_error"
    user_message = "Something went wrong while checking your step. Please try again."


def _classification_for_input_error(exc: MathInputError) -> dict:
    return {
        "error_type": exc.category,
        "confidence": "high",
        "reason": exc.user_message,
    }


def _user_safe_hint_for_input_error(exc: MathInputError) -> str:
    return exc.user_message


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SymPy helpers
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def _run_timed(func: Callable[..., T], *args, timeout: float = _NORMALIZE_TIMEOUT_SEC, **kwargs) -> T:
    future = _EXECUTOR.submit(func, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeoutError as exc:
        raise EvaluationTimeoutError(
            f"Timed out after {timeout}s: {func.__name__}"
        ) from exc


def _scan_text_for_input_issues(expression: str) -> None:
    if not expression or not expression.strip():
        raise MalformedSyntaxError("Empty expression", user_message="Enter an expression to check.")

    if contains_text_like_input(expression):
        raise MalformedSyntaxError(
            "Plain text and word-like input are not allowed.",
            user_message="Use a math expression, not plain text or words.",
        )

    if _DIV_ZERO_PATTERN.search(expression):
        raise DivisionByZeroError(
            "Division by zero detected in input",
            user_message=DivisionByZeroError.user_message,
        )

    for pattern, detail in _UNDEFINED_TEXT_PATTERNS:
        if pattern.search(expression):
            raise UndefinedMathError(detail, user_message=UndefinedMathError.user_message)


def _sympify_safe(cleaned: str, original: str) -> Expr: #This function is used to safely convert a string to a SymPy expression.
    try:
        return sympify(cleaned, locals=_SYMPY_LOCALS)
    except SympifyError as exc:
        msg = str(exc).lower()
        if "undefined" in msg or "not defined" in msg:
            raise UndefinedSymbolError(
                str(exc),
                user_message=UndefinedSymbolError.user_message,
            ) from exc
        raise MalformedSyntaxError(
            str(exc),
            user_message=MalformedSyntaxError.user_message,
        ) from exc
    except SyntaxError as exc:
        raise MalformedSyntaxError(
            str(exc),
            user_message=MalformedSyntaxError.user_message,
        ) from exc
    except TypeError as exc:
        raise MalformedSyntaxError(
            str(exc),
            user_message="Check that numbers and symbols are combined with valid operators.",
        ) from exc
    except ZeroDivisionError as exc:
        raise DivisionByZeroError(str(exc)) from exc
    except ValueError as exc:
        raise MalformedSyntaxError(
            str(exc),
            user_message=MalformedSyntaxError.user_message,
        ) from exc


def _ensure_algebraically_defined(expr: Expr) -> None:
    """Reject expressions that simplify to non-finite undefined forms."""
    if expr.has(zoo) or expr.has(nan):
        raise UndefinedMathError(
            "Expression contains undefined value (zoo/nan)",
            user_message=UndefinedMathError.user_message,
        )

    try:
        check = _run_timed(simplify, expr, timeout=3.0)
    except EvaluationTimeoutError:
        return
    except (ZeroDivisionError, ValueError) as exc:
        raise UndefinedMathError(str(exc)) from exc

    if check is zoo or check is nan:
        raise UndefinedMathError(
            "Expression simplifies to an undefined value",
            user_message=UndefinedMathError.user_message,
        )


def _expr_display(expr: Expr) -> str:
    """Prefer LaTeX for API-facing structural diff strings."""
    try:
        from sympy import latex
        return latex(expr)
    except Exception:
        return str(expr)


def _format_symbol_key(key: str) -> str:
    if key == "1":
        return "the constant term"
    return f"the {key} term"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# HINT ENGINE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
_HINT_LEVELS: dict[str, dict[int, str]] = {
    "sign_error": {
        1: "Check the sign on {focus} â€” a plus/minus mix-up is common here.",
        2: "Focus on {focus}: does your coefficient have the opposite sign from what you intended?",
    },
    "arithmetic_error": {
        1: "Recalculate the coefficient on {focus}; the value looks off.",
        2: "Work through the arithmetic for {focus} again, one operation at a time.",
    },
    "distribution_error": {
        1: "When you multiply, each term inside the parentheses must be included.",
        2: "Your expansion may be missing a piece â€” multiply through each term inside the parentheses separately.",
    },
    "unknown": {
        1: "Compare your step to the previous line term by term.",
        2: "Re-check each term and coefficient; one part of the expression does not match.",
    },
    "no_progress": {
        1: "You submitted the same expression. Apply the next algebraic step.",
        2: "Try transforming the current line before submitting again.",
    },
    "term_reorder": {
        1: "Reordering terms is a valid rewrite, but it is not the next solving step. Apply the required operation.",
        2: "The expression is equivalent to the current line â€” expand or simplify to move forward.",
    },
}


def _hint_focus_from_diff(structural_diff: dict | None, error_type: str) -> str:
    if not structural_diff:
        return "one part of your expression"

    coeff_diff = structural_diff.get("coeff_diff", {})
    if coeff_diff:
        key = next(iter(coeff_diff))
        return _format_symbol_key(key)

    missing = structural_diff.get("term_diff", {}).get("missing_terms", [])
    if missing and error_type == "distribution_error":
        return "a term from your expansion"

    return "one part of your expression"


def generate_hint(
    error_type: str,
    structural_diff: dict | None = None,
    hint_level: int = 1,
) -> str:
    """
    Return a student-facing hint. Level 2 goes deeper; session-based graduation
    is TODO (Phase 5): wire hint_level to attempt count from the session store.
    """
    level = max(1, min(hint_level, 2))
    templates = _HINT_LEVELS.get(error_type, _HINT_LEVELS["unknown"])
    template = templates.get(level, templates[1])
    focus = _hint_focus_from_diff(structural_diff, error_type)
    return template.format(focus=focus)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# STEP VALIDATOR
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
class StepValidator:
    """This class is used to validate a step of a problem."""

    def parser(self, expression: str) -> Expr:
        _scan_text_for_input_issues(expression)

        cleaned = preprocess_for_sympy(expression)
        i = 0
        while i < len(cleaned) - 1:
            ch = cleaned[i]
            nxt = cleaned[i + 1]
            if ch in "+-*/" and nxt in "*/" and not (ch == "*" and nxt == "*"):
                raise MalformedSyntaxError(
                    f"Consecutive operators at position {i}: '{ch}{nxt}'",
                    user_message=f"Invalid operators near position {i + 1} ('{ch}{nxt}').",
                )
            i += 1

        expr = _sympify_safe(cleaned, expression)
        _ensure_algebraically_defined(expr)
        return expr

    def normalize(self, expr: Expr) -> Expr: # cannonical form of the expression ;
        if isinstance(expr, Relational):
            return expr

        def _pipeline(e: Expr) -> Expr:
            normalized = expand(e)
            for sym in normalized.free_symbols:
                normalized = collect(normalized, sym)
            # collect() can factor polynomials (e.g. 7x^2+x â†’ x*(7x+1)), which
            # breaks structural term/coefficient comparison â€” re-expand to sum form.
            return expand(simplify(normalized))

        return _run_timed(_pipeline, expr)

    @staticmethod
    def _get_terms(expr: Expr) -> set:
        return set(expr.args) if isinstance(expr, Add) else {expr}

    def _extract_structural_diff(self, student: Expr, expected: Expr) -> dict:
        # this function is used to extract the structural diff between the student's and expected expressions.
        student_op = type(student).__name__
        expected_op = type(expected).__name__

        student_terms = self._get_terms(student)
        expected_terms = self._get_terms(expected)

        missing_terms = [_expr_display(t) for t in expected_terms - student_terms]
        extra_terms = [_expr_display(t) for t in student_terms - expected_terms]

        student_coeffs = student.as_coefficients_dict()
        expected_coeffs = expected.as_coefficients_dict()

        all_keys = set(student_coeffs) | set(expected_coeffs)
        coeff_diff: dict[str, dict] = {}
        for key in all_keys:
            s_val = student_coeffs.get(key, 0)
            e_val = expected_coeffs.get(key, 0)
            if simplify(s_val - e_val) != 0:
                coeff_diff[str(key)] = {
                    "student": str(s_val),
                    "expected": str(e_val),
                }

        same_monomial_basis = set(student_coeffs.keys()) == set(expected_coeffs.keys())

        return {
            "top_level_op": {
                "student": student_op,
                "expected": expected_op,
                "match": student_op == expected_op,
            },
            "term_diff": {
                "missing_terms": missing_terms,
                "extra_terms": extra_terms,
            },
            "coeff_diff": coeff_diff,
            "same_monomial_basis": same_monomial_basis,
        }

    def comparison(self, student_str: str, expected_str: str) -> dict:
        student_parsed = self.parser(student_str)
        expected_parsed = self.parser(expected_str)
        student_parsed = _align_student_symbols_to_reference(student_parsed, expected_parsed)

        if isinstance(student_parsed, Relational) or isinstance(expected_parsed, Relational):
            is_equivalent = student_parsed == expected_parsed
            return {
                "is_equivalent": bool(is_equivalent),
                "structural_diff": {
                    "top_level_op": {
                        "student": type(student_parsed).__name__,
                        "expected": type(expected_parsed).__name__,
                        "match": type(student_parsed) == type(expected_parsed),
                    },
                    "term_diff": {"missing_terms": [], "extra_terms": []},
                    "coeff_diff": {},
                    "same_monomial_basis": is_equivalent,
                },
            }

        student_expr = self.normalize(student_parsed)
        expected_expr = self.normalize(expected_parsed)

        is_equivalent = _run_timed(
            lambda: simplify(student_expr - expected_expr) == 0,
            timeout=5.0,
        )
        structural_diff = self._extract_structural_diff(student_expr, expected_expr)

        return {
            "is_equivalent": bool(is_equivalent),
            "structural_diff": structural_diff,
        }

    def _parse_internal(self, expr_str: str) -> Expr:
        return self.parser(expr_str.replace("**", "^"))

    @staticmethod
    def _is_constant_only_term_noise(
        missing_terms: list[str],
        extra_terms: list[str],
    ) -> bool:
        """SymPy sometimes swaps explicit constant terms (e.g. +1 vs +2) without
        dropping a monomial â€” not a missing-term distribution mistake."""
        from sympy import sympify as _sympify

        if not missing_terms or not extra_terms:
            return False

        for term_str in missing_terms + extra_terms:
            try:
                if not _sympify(term_str).is_Number:
                    return False
            except (SympifyError, TypeError, ValueError):
                return False
        return True

    def _is_distribution_error(self, structural_diff: dict) -> bool:
        missing_terms = structural_diff["term_diff"]["missing_terms"]
        if not missing_terms:
            return False

        extra_terms = structural_diff["term_diff"]["extra_terms"]
        if self._is_constant_only_term_noise(missing_terms, extra_terms):
            return False

        if structural_diff.get("same_monomial_basis", False):
            return False

        # NEW GUARD: if every missing term has a corresponding extra term
        # that shares the same monomial base (differing only by sign or
        # coefficient), this is a sign/arithmetic error, not a missing term.
        if len(missing_terms) == len(extra_terms) and len(missing_terms) > 0:
            from sympy import sympify, Symbol
            try:
                pairs_match = all(
                    sympify(m).as_coefficients_dict().keys() ==
                    sympify(e).as_coefficients_dict().keys()
                    for m, e in zip(sorted(missing_terms), sorted(extra_terms))
                )
                if pairs_match:
                    return False
            except Exception:
                pass

        return True

    def classify_error(self, structural_diff: dict) -> dict:
        coeff_diff = structural_diff.get("coeff_diff", {})
        missing_terms = structural_diff["term_diff"]["missing_terms"]
        extra_terms = structural_diff["term_diff"]["extra_terms"]

        if self._is_distribution_error(structural_diff):
            return {
                "error_type": "distribution_error",
                "confidence": "high",
                "reason": "One or more terms are missing after expansion.",
            }

        if coeff_diff:
            all_sign_flips = all(
                simplify(
                    self._parse_internal(v["student"])
                    + self._parse_internal(v["expected"])
                )
                == 0
                for v in coeff_diff.values()
            )
            if all_sign_flips:
                keys = [_format_symbol_key(k) for k in coeff_diff]
                return {
                    "error_type": "sign_error",
                    "confidence": "high",
                    "reason": f"Sign may be flipped on: {', '.join(keys)}",
                }

        if coeff_diff:
            confidence = "medium" if extra_terms else "high"
            keys = [_format_symbol_key(k) for k in coeff_diff]
            return {
                "error_type": "arithmetic_error",
                "confidence": confidence,
                "reason": f"Coefficient mismatch on: {', '.join(keys)}",
            }

        return {
            "error_type": "unknown",
            "confidence": "low",
            "reason": "Expressions differ but no specific error pattern was detected.",
        }

    def validate(self, student_str: str, expected_str: str) -> dict:
        comparison_result = self.comparison(student_str, expected_str)
        is_equivalent = comparison_result["is_equivalent"]
        structural_diff = comparison_result["structural_diff"]

        if is_equivalent:
            return {
                "is_equivalent": True,
                "structural_diff": structural_diff,
                "error_classification": None,
                "hint": "Correct! Well done.",
            }

        error_classification = self.classify_error(structural_diff)
        hint = generate_hint(
            error_classification["error_type"],
            structural_diff=structural_diff,
            hint_level=1,
        )

        return {
            "is_equivalent": False,
            "structural_diff": structural_diff,
            "error_classification": error_classification,
            "hint": hint,
        }


_validator = StepValidator()


def _handle_step_validation(data: StepInput) -> StepResult:
    expected = data.expected or ""
    try:
        result = _validator.validate(data.step, expected)
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=expected,
            **result,
        )
    except MathInputError as exc:
        logger.info("Input rejected [%s]: %s", exc.category, exc)
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=expected,
            is_equivalent=False,
            structural_diff=None,
            error_classification=_classification_for_input_error(exc),
            hint=_user_safe_hint_for_input_error(exc),
        )
    except Exception as exc:
        logger.exception("Unhandled engine error")
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=expected,
            is_equivalent=False,
            structural_diff=None,
            error_classification={
                "error_type": EngineError.category,
                "confidence": "low",
                "reason": EngineError.user_message,
            },
            hint=EngineError.user_message,
        )


def _apply_session_hint_policy(session: SessionState, result: StepResult) -> StepResult:
    """Escalate hint level, regenerate hints, and reveal solution per session rules."""
    if (
        not result.is_equivalent
        and session.incorrect_attempt_count >= MAX_ATTEMPTS_BEFORE_ESCALATION
        and session.hint_level == 1
    ):
        session.hint_level = 2

    hint = result.hint
    if (
        not result.is_equivalent
        and result.structural_diff is not None
        and result.error_classification is not None
    ):
        hint = generate_hint(
            result.error_classification["error_type"],
            structural_diff=result.structural_diff,
            hint_level=session.hint_level,
        )

    if (
        not result.is_equivalent
        and session.incorrect_attempt_count >= MAX_ATTEMPTS_BEFORE_REVEAL
    ):
        hint = f"{hint} â€” Solution: {session.expected_final}"

    return result.model_copy(update={"hint": hint})


def _problem_to_response(row: Problem) -> ProblemResponse:
    return ProblemResponse(
        id=row.id,
        expression=row.expression,
        expected_final=row.expected_final,
        difficulty=row.difficulty,
        topic=row.topic,
        created_at=row.created_at,
    )


def _problem_id_from_expression(expression: str) -> str:
    digest = sha256(expression.encode("utf-8")).hexdigest()[:16]
    return f"user_{digest}"


def _get_primary_solution_steps(db: OrmSession, problem_id: str) -> list[SolutionStep]:
    path = (
        db.query(SolutionPath)
        .filter_by(problem_id=problem_id, is_primary=True)
        .first()
    )
    if path is None:
        return []
    return (
        db.query(SolutionStep)
        .filter_by(path_id=path.sol_path_id)
        .order_by(SolutionStep.step_order.asc())
        .all()
    )


def _ensure_solution_steps(
    db: OrmSession,
    problem_id: str,
    steps: list[str],
) -> list[SolutionStep]:
    path = (
        db.query(SolutionPath)
        .filter_by(problem_id=problem_id, is_primary=True)
        .first()
    )
    if path is None:
        path = SolutionPath(problem_id=problem_id, sol_path_name="default", is_primary=True)
        db.add(path)
        db.flush()

    for index, step in enumerate(steps, start=1):
        row = (
            db.query(SolutionStep)
            .filter_by(path_id=path.sol_path_id, step_order=index)
            .first()
        )
        if row is None:
            db.add(
                SolutionStep(
                    path_id=path.sol_path_id,
                    step_order=index,
                    sol_step_expression=step,
                )
            )
    db.flush()
    return _get_primary_solution_steps(db, problem_id)


def _expression_equivalent(a: str, b: str) -> bool:
    return _validator.comparison(a, b)["is_equivalent"]


def _canonical_step_display_safe(expression: str) -> str | None:
    try:
        return canonical_step_display(expression)
    except (UnsupportedProblemError, MathInputError):
        return None


def _is_term_reorder_submission(step: str, current_expression: str, expected_step: str) -> bool:
    """
  Return True when ``step`` is the same canonical line as ``current_expression``
  (e.g. factor reorder) but not the immediate expected next step.
    """
    if is_factor_reorder_submission(step, current_expression):
        return not _strict_canonical_step_match(step, expected_step)

    step_canon = _canonical_step_display_safe(step)
    current_canon = _canonical_step_display_safe(current_expression)
    if step_canon is None or current_canon is None or step_canon != current_canon:
        return False
    return not _strict_canonical_step_match(step, expected_step)


def _current_step_index(session_row: TutoringSession, steps: list[SolutionStep]) -> int:
    """
    Return the 0-based index of the solution step the student is working toward.

    ``current_step_id`` NULL means step_order 1; otherwise it holds the FK of the
    next expected step (set after each correct submission).
    """
    if session_row.current_step_id is None:
        return 0
    for idx, row in enumerate(steps):
        if row.sol_step_id == session_row.current_step_id:
            return idx
    return 0


def _expected_step_for_session(
    session_row: TutoringSession, steps: list[SolutionStep]
) -> str:
    index = _current_step_index(session_row, steps)
    return steps[index].sol_step_expression


def _strict_canonical_step_match(step: str, expected: str) -> bool:
    try:
        return canonical_step_display(step) == canonical_step_display(expected)
    except UnsupportedProblemError:
        return False


def _matches_immediate_canonical_step(
    step: str,
    expected: str,
    steps: list[SolutionStep],
    current_index: int,
) -> bool:
    if _strict_canonical_step_match(step, expected):
        return True
    try:
        if not _expression_equivalent(step, expected):
            return False
    except MathInputError:
        return False
    for idx in range(current_index + 1, len(steps)):
        try:
            if _expression_equivalent(step, steps[idx].sol_step_expression):
                if not _strict_canonical_step_match(step, expected):
                    return False
        except MathInputError:
            continue
    return True


def _validate_immediate_step(
    data: StepInput,
    expected: str,
    steps: list[SolutionStep],
    current_index: int,
) -> StepResult:
    if _matches_immediate_canonical_step(data.step, expected, steps, current_index):
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=expected,
            is_equivalent=True,
            structural_diff=None,
            error_classification=None,
            hint="Correct! Well done.",
        )
    return _handle_step_validation(
        StepInput(session_id=data.session_id, step=data.step, expected=expected)
    )


def _find_skip_ahead_target(
    step: str,
    steps: list[SolutionStep],
    current_index: int,
) -> int | None:
    """Return the furthest future canonical step index matching ``step``, if any."""
    target_index: int | None = None
    for idx in range(current_index + 1, len(steps)):
        try:
            if _expression_equivalent(step, steps[idx].sol_step_expression):
                target_index = idx
        except MathInputError:
            continue
    return target_index


def _build_skip_ahead_info(
    steps: list[SolutionStep],
    current_index: int,
    target_index: int,
) -> tuple[list[SkippedStepInfo], str]:
    skipped = [
        SkippedStepInfo(
            step_order=steps[idx].step_order,
            expected=steps[idx].sol_step_expression,
        )
        for idx in range(current_index, target_index)
    ]
    if len(skipped) == 1:
        skip = skipped[0]
        message = (
            f"You skipped step {skip.step_order} (expected: {skip.expected}). "
            "Continuing from your answer."
        )
    else:
        parts = ", ".join(
            f"step {item.step_order} (expected: {item.expected})" for item in skipped
        )
        message = f"You skipped {parts}. Continuing from your answer."
    return skipped, message


@app.get("/problem/{problem_id}", response_model=ProblemResponse)
def get_problem(problem_id: str, db: OrmSession = Depends(get_db)):
    """
    Fetch a single problem by its primary-key ID.

    Inputs: path parameter ``problem_id`` (e.g. ``dist_001``).
    Returns: ProblemResponse with expression, expected_final, difficulty, topic.
    Raises HTTP 404 if no row exists for that ID.
    """
    row = db.query(Problem).filter_by(id=problem_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "Problem not found"})
    return _problem_to_response(row)


@app.get("/sample-problem", response_model=ProblemResponse)
def get_sample_problem(
    difficulty: str | None = None,
    topic: str | None = None,
    db: OrmSession = Depends(get_db),
):
    """
    Return one random problem from the library, optionally filtered.

    Query params (all optional):
      - difficulty: ``easy``, ``medium``, or ``hard`` (case-insensitive)
      - topic: e.g. ``distribution`` or ``simplification`` (case-insensitive)

    Returns: ProblemResponse for a single randomly selected matching row.
    Raises HTTP 404 when no problems match the given filters.
    """
    query = db.query(Problem)
    if difficulty is not None:
        query = query.filter(func.lower(Problem.difficulty) == difficulty.lower())
    if topic is not None:
        query = query.filter(func.lower(Problem.topic) == topic.lower())

    row = query.order_by(func.random()).limit(1).first()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "No problems found matching the given filters."},
        )
    return _problem_to_response(row)


@app.post("/problem", response_model=ProblemResponse, status_code=201)
def create_problem(
    data: ProblemCreateRequest,
    db: OrmSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """
    Insert a new problem into the library (admin use; no auth yet).

    Body: ProblemCreateRequest with id, expression, expected_final, optional
    difficulty and topic.
    Returns: HTTP 201 with ProblemResponse on success.
    Raises HTTP 409 if the ID already exists, HTTP 500 on unexpected DB errors.
    """
    if not data.expression.strip() or not data.expected_final.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": "expression and expected_final must be non-empty strings."},
        )

    try:
        existing = db.query(Problem).filter_by(id=data.id).first()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail={"error": "A problem with this ID already exists."},
            )

        row = Problem(
            id=data.id,
            expression=data.expression,
            expected_final=data.expected_final,
            difficulty=data.difficulty,
            topic=data.topic,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _problem_to_response(row)
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to create problem")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to create problem. Please try again."},
        ) from None


@app.post("/start-session", response_model=StartSessionResponse)
def start_session(
    data: StartSessionRequest,
    db: OrmSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    try:
        session_id = str(uuid.uuid4())
        now = _utc_now()
        subject = "algebra"
        topic: str | None = None

        if data.problem_expression is not None:
            if not data.problem_expression.strip():
                raise HTTPException(
                    status_code=422,
                    detail={"error": "problem_expression must be a non-empty string."},
                )
            try:
                plan = build_solution_plan(data.problem_expression)
            except UnsupportedProblemError as exc:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "unsupported_problem",
                        "message": str(exc),
                        "supported_topics": [
                            "distribution",
                            "foil",
                            "simplification",
                            "linear_steps",
                        ],
                    },
                ) from exc

            problem_expression = canonical_step_display(data.problem_expression.strip())
            expected_final = plan.final_answer
            subject = plan.subject
            topic = plan.topic
            problem_id = data.problem_id or _problem_id_from_expression(problem_expression)
            stmt = (
                insert(Problem)
                .values(
                    id=problem_id,
                    expression=problem_expression,
                    expected_final=expected_final,
                    topic=topic,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "expression": problem_expression,
                        "expected_final": expected_final,
                        "topic": topic,
                    },
                )
            )
            db.execute(stmt)
            steps = _ensure_solution_steps(db, problem_id, plan.steps)
        else:
            if not data.problem_id:
                raise HTTPException(
                    status_code=422,
                    detail={"error": "Provide either problem_expression or problem_id."},
                )
            problem_row = db.query(Problem).filter_by(id=data.problem_id).first()
            if problem_row is None:
                raise HTTPException(
                    status_code=404,
                    detail={"error": "Problem not found."},
                )
            problem_expression = canonical_step_display(problem_row.expression)
            expected_final = problem_row.expected_final
            topic = problem_row.topic
            problem_id = problem_row.id
            steps = _get_primary_solution_steps(db, problem_id)
            if not steps:
                steps = _ensure_solution_steps(db, problem_id, [expected_final])

        db.add(
            TutoringSession(
                session_id=session_id,
                problem_id=problem_id,
                attempt_count=0,
                incorrect_attempt_count=0,
                hint_level=1,
                created_at=now,
                last_active=now,
                current_step_id=None,
                current_expression=problem_expression,
                completed=False,
                user_id=current_user.id if current_user else None,
            )
        )
        db.commit()

        return StartSessionResponse(
            session_id=session_id,
            problem_id=problem_id,
            problem_expression=problem_expression,
            expected_final=expected_final,
            message="Session started. Submit your first step.",
            subject=subject,
            topic=topic,
            current_expression=problem_expression,
            step_count=len(steps),
        )
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to start session")
        return StartSessionResponse(
            session_id="",
            problem_id=data.problem_id or "",
            problem_expression=data.problem_expression or "",
            expected_final=data.expected_final or "",
            message="Something went wrong while starting the session. Please try again.",
        )


@app.post("/submit-step", response_model=StepResult)
def submit_step(
    data: StepInput,
    db: OrmSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    session_row = (
        db.query(TutoringSession).filter_by(session_id=data.session_id).first()
    )
    if session_row is None:
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=data.expected or "",
            is_equivalent=False,
            structural_diff=None,
            error_classification=None,
            hint="Session not found. Please start a new session.",
        )

    _assert_session_access(session_row, current_user)

    problem_row = db.query(Problem).filter_by(id=session_row.problem_id).first()
    if problem_row is None:
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=data.expected or "",
            is_equivalent=False,
            structural_diff=None,
            error_classification=None,
            hint="Session not found. Please start a new session.",
        )
    steps = _get_primary_solution_steps(db, session_row.problem_id)
    if not steps:
        steps = _ensure_solution_steps(db, session_row.problem_id, [problem_row.expected_final])
    step_count = len(steps)

    if session_row.completed:
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=problem_row.expected_final,
            is_equivalent=True,
            structural_diff=None,
            error_classification=None,
            hint="Session already completed.",
            step_index=step_count,
            step_count=step_count,
            is_final_step=True,
            session_complete=True,
            current_expression=session_row.current_expression,
        )

    current_index = _current_step_index(session_row, steps)
    expected_step = steps[current_index].sol_step_expression
    is_final_step = current_index == (step_count - 1)

    # no-progress submission: same expression as the current line (exact, not merely equivalent)
    if data.step.strip() == session_row.current_expression.strip():
            hint = generate_hint("no_progress", hint_level=session_row.hint_level)
            result = StepResult(
                session_id=data.session_id,
                received_step=data.step,
                expected_step=expected_step,
                is_equivalent=False,
                structural_diff=None,
                error_classification={
                    "error_type": "no_progress",
                    "confidence": "high",
                    "reason": "Submission matches the current expression.",
                },
                hint=hint,
                step_index=current_index + 1,
                step_count=step_count,
                is_final_step=False,
                session_complete=False,
                current_expression=session_row.current_expression,
            )
            attempt_ts = _utc_now()  
            db.add(
                Attempt(
                    session_id=session_row.session_id,
                    step=data.step,
                    expected=expected_step,
                    is_equivalent=False,
                    error_type="no_progress",
                    hint=hint,
                    step_order=current_index + 1,
                    timestamp=attempt_ts,
                )
            )
            session_row.attempt_count = session_row.attempt_count + 1
            session_row.last_active = attempt_ts
            db.commit()
            return result

    # Reordering-only: same canonical line as current, not the expected next step.
    if _is_term_reorder_submission(data.step, session_row.current_expression, expected_step):
        hint = generate_hint("term_reorder", hint_level=session_row.hint_level)
        result = StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=expected_step,
            is_equivalent=False,
            structural_diff=None,
            error_classification={
                "error_type": "term_reorder",
                "confidence": "high",
                "reason": "Submission is equivalent to the current expression but not the next step.",
            },
            hint=hint,
            step_index=current_index + 1,
            step_count=step_count,
            is_final_step=False,
            session_complete=False,
            current_expression=session_row.current_expression,
        )
        attempt_ts = _utc_now()
        db.add(
            Attempt(
                session_id=session_row.session_id,
                step=data.step,
                expected=expected_step,
                is_equivalent=False,
                error_type="term_reorder",
                hint=hint,
                step_order=current_index + 1,
                timestamp=attempt_ts,
            )
        )
        session_row.attempt_count = session_row.attempt_count + 1
        session_row.last_active = attempt_ts
        db.commit()
        return result

    skip_target_index: int | None = None
    skipped_steps: list[SkippedStepInfo] | None = None
    skip_message: str | None = None
    if not is_final_step:
        skip_target_index = _find_skip_ahead_target(data.step, steps, current_index)
        if skip_target_index is not None and _strict_canonical_step_match(
            data.step, expected_step
        ):
            skip_target_index = None
        if skip_target_index is not None:
            skipped_steps, skip_message = _build_skip_ahead_info(
                steps, current_index, skip_target_index
            )
            result = StepResult(
                session_id=data.session_id,
                received_step=data.step,
                expected_step=expected_step,
                is_equivalent=True,
                structural_diff=None,
                error_classification=None,
                hint="Correct! Well done.",
                skipped_steps=skipped_steps,
                skip_message=skip_message,
            )
        else:
            result = _validate_immediate_step(
                StepInput(session_id=data.session_id, step=data.step, expected=expected_step),
                expected_step,
                steps,
                current_index,
            )
    else:
        result = _validate_immediate_step(
            StepInput(session_id=data.session_id, step=data.step, expected=expected_step),
            expected_step,
            steps,
            current_index,
        )

    session_obj = SessionState(
        session_id=session_row.session_id,
        problem_id=session_row.problem_id,
        problem_expression=problem_row.expression,
        expected_final=problem_row.expected_final,
        attempt_count=session_row.attempt_count + 1,
        incorrect_attempt_count=session_row.incorrect_attempt_count
        + (
            0
            if result.is_equivalent
            or (result.error_classification and result.error_classification["error_type"] in {
                "invalid_input",
                "malformed_syntax",
                "invalid_format",
                "division_by_zero",
                "undefined_math",
                "undefined_symbol",
                "evaluation_timeout",
                "engine_error",
            })
            else 1
        ),
        hint_level=session_row.hint_level,
        attempt_history=[],
    )
    result = _apply_session_hint_policy(session_obj, result)

    session_row.attempt_count = session_obj.attempt_count
    session_row.incorrect_attempt_count = session_obj.incorrect_attempt_count
    session_row.hint_level = session_obj.hint_level
    session_row.last_active = _utc_now()

    session_complete = False
    if result.is_equivalent:
        try:
            session_row.current_expression = canonical_step_display(data.step)
        except UnsupportedProblemError:
            session_row.current_expression = data.step
        if skip_target_index is not None:
            if skip_target_index == step_count - 1:
                session_row.completed = True
                session_complete = True
                session_row.current_step_id = steps[-1].sol_step_id
            else:
                session_row.current_step_id = steps[skip_target_index + 1].sol_step_id
        elif is_final_step:
            session_row.completed = True
            session_complete = True
            session_row.current_step_id = steps[-1].sol_step_id
        else:
            next_row = steps[current_index + 1]
            session_row.current_step_id = next_row.sol_step_id

    attempt_ts = _utc_now()
    db.add(
        Attempt(
            session_id=session_row.session_id,
            step=data.step,
            expected=expected_step,
            is_equivalent=result.is_equivalent,
            error_type=(
                result.error_classification.get("error_type")
                if result.error_classification
                else None
            ),
            hint=result.hint,
            step_order=current_index + 1,
            timestamp=attempt_ts,
        )
    )
    db.commit()
    response_index = step_count if session_complete else current_index + 1
    if skip_target_index is not None:
        response_index = skip_target_index + 1
    return result.model_copy(
        update={
            "step_index": response_index,
            "step_count": step_count,
            "is_final_step": session_complete,
            "session_complete": session_complete,
            "current_expression": session_row.current_expression,
            "skipped_steps": skipped_steps,
            "skip_message": skip_message,
        }
    )


@app.get("/session/{session_id}")
def get_session(
    session_id: str,
    db: OrmSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    session_row = (
        db.query(TutoringSession).filter_by(session_id=session_id).first()
    )
    if session_row is None:
        return {"error": "Session not found"}

    _assert_session_access(session_row, current_user)

    problem_row = db.query(Problem).filter_by(id=session_row.problem_id).first()
    problem_expression = ""
    expected_final: str | None = None
    topic: str | None = None
    if problem_row:
        problem_expression = (
            _canonical_step_display_safe(problem_row.expression)
            or problem_row.expression
        )
        expected_final = (
            _canonical_step_display_safe(problem_row.expected_final)
            or problem_row.expected_final
        )
        topic = problem_row.topic

    stored_current = getattr(session_row, "current_expression", problem_expression)
    current_expression = _canonical_step_display_safe(stored_current) or stored_current

    steps = _get_primary_solution_steps(db, session_row.problem_id)
    step_count = len(steps) if steps else 1
    step_index = step_index_for_session(session_row, steps)

    attempt_rows = (
        db.query(Attempt)
        .filter_by(session_id=session_id)
        .order_by(Attempt.timestamp.asc())
        .all()
    )
    attempt_history = [
        {
            "step": row.step,
            "expected": row.expected,
            "step_order": row.step_order if hasattr(row, "step_order") else 1,
            "is_equivalent": row.is_equivalent,
            "error_type": row.error_type,
            "hint": row.hint,
            "timestamp": row.timestamp,
        }
        for row in attempt_rows
    ]

    return SessionSummary(
        session_id=session_row.session_id,
        problem_id=session_row.problem_id,
        problem_expression=problem_expression,
        attempt_count=session_row.attempt_count,
        hint_level=session_row.hint_level,
        completed=getattr(session_row, "completed", False),
        current_expression=current_expression,
        attempt_history=attempt_history,
        created_at=session_row.created_at,
        last_active=session_row.last_active,
        expected_final=expected_final,
        topic=topic,
        step_index=step_index,
        step_count=step_count,
        incorrect_attempt_count=session_row.incorrect_attempt_count,
    )


@app.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    db: OrmSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    session_row = (
        db.query(TutoringSession).filter_by(session_id=session_id).first()
    )
    if session_row is None:
        return {"deleted": False, "error": "Session not found"}

    _assert_session_access(session_row, current_user)

    db.query(Attempt).filter_by(session_id=session_id).delete()
    db.delete(session_row)
    db.commit()
    return {"deleted": True}


@app.get("/health")
def health():
    """Liveness probe â€” no database check."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness probe â€” verifies database connectivity."""
    if not check_db_connection():
        raise HTTPException(
            status_code=503,
            detail={"status": "unavailable", "db": "disconnected"},
        )
    return {"status": "ok", "db": "connected"}


@app.get("/")
def root():
    return {"status": "MathAssistant backend is running!", "version": "1.0.0"}
