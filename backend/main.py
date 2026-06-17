"""
MathAssistant – FastAPI + SymPy tutoring backend
=================================================
Data flow (one request):

  raw student string  (^ for exponents, e.g. x^2 — not **)
       │
       ▼
  [PARSING LAYER]        parser()              pre-process & sympify
       │
       ▼
  [NORMALIZATION LAYER]  normalize()           expand → collect → simplify
       │
       ▼
  [COMPARISON LAYER]     comparison()          equivalence check + structural diff
       │
       ▼
  [CLASSIFICATION LAYER] classify_error()      deterministic rule-based error taxonomy
       │
       ▼
  [HINT ENGINE]          generate_hint()       error_type → hint string
       │
       ▼
  JSON response

Note: solve(), integrate(), and diff() are not used on the MVP validation path.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, TypeVar

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession 
from pydantic import BaseModel
from sympy import (
    Add, E, Mul, Pow,
    expand, collect, simplify, sympify,
    zoo, nan, oo,
)
from sympy.core.expr import Expr
from sympy.core.sympify import SympifyError

from db.database import check_db_connection, get_db, init_db
from db.models import Attempt, Problem, TutoringSession

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

# ──────────────────────────────────────────────────────────────────────────────
# App bootstrap
# ──────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MathAssistant", version="0.2.1", lifespan=lifespan)

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# Request / response models
# ──────────────────────────────────────────────────────────────────────────────
class StepInput(BaseModel):
    session_id: str
    step: str
    expected: str


class StepResult(BaseModel):
    session_id: str
    received_step: str
    expected_step: str
    is_equivalent: bool
    structural_diff: dict | None
    error_classification: dict | None
    hint: str


class StartSessionRequest(BaseModel):
    problem_id: str
    problem_expression: str | None = None
    expected_final: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    problem_id: str
    problem_expression: str
    expected_final: str
    message: str


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
    attempt_history: list[dict]
    created_at: datetime
    last_active: datetime


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
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)


# ──────────────────────────────────────────────────────────────────────────────
# Input / engine exceptions (never expose raw SymPy messages to students)
# ──────────────────────────────────────────────────────────────────────────────
class MathInputError(ValueError):
    """Base for user-input problems detected before or during parsing."""

    category = "invalid_input"
    user_message = "That expression could not be read. Check your notation."

    def __init__(self, message: str, *, user_message: str | None = None):
        super().__init__(message)
        if user_message is not None:
            self.user_message = user_message


class ParseError(MathInputError):
    """Legacy alias — malformed or unsupported input."""

    category = "malformed_syntax"


class InvalidFormatError(ParseError):
    """Correct domain but wrong notation (e.g. ** instead of ^)."""

    category = "invalid_format"


class MalformedSyntaxError(ParseError):
    """Syntactically broken input."""

    category = "malformed_syntax"
    user_message = "Check operators and parentheses — something in the syntax is invalid."


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
    """Unexpected internal failure — logged, generic message to client."""

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


# ══════════════════════════════════════════════════════════════════════════════
# SymPy helpers
# ══════════════════════════════════════════════════════════════════════════════
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
        return sympify(cleaned, locals={"e": E})
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


# ══════════════════════════════════════════════════════════════════════════════
# HINT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
_HINT_LEVELS: dict[str, dict[int, str]] = {
    "sign_error": {
        1: "Check the sign on {focus} — a plus/minus mix-up is common here.",
        2: "Focus on {focus}: does your coefficient have the opposite sign from what you intended?",
    },
    "arithmetic_error": {
        1: "Recalculate the coefficient on {focus}; the value looks off.",
        2: "Work through the arithmetic for {focus} again, one operation at a time.",
    },
    "distribution_error": {
        1: "When you multiply, each term inside the parentheses must be included.",
        2: "Your expansion may be missing a piece — multiply through each term inside the parentheses separately.",
    },
    "unknown": {
        1: "Compare your step to the previous line term by term.",
        2: "Re-check each term and coefficient; one part of the expression does not match.",
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


# ══════════════════════════════════════════════════════════════════════════════
# STEP VALIDATOR
# ══════════════════════════════════════════════════════════════════════════════
class StepValidator:
    """This class is used to validate a step of a problem."""

    def parser(self, expression: str) -> Expr:
        if "**" in expression: # does this even matter? "**" and "^" should be accepted equally; perhaps this InvalidFormatError should be removed post-MVP.
            raise InvalidFormatError(
                "Use ^ for exponents (e.g. x^2), not **",
                user_message="Use ^ for exponents (e.g. x^2), not **.",
            )

        _scan_text_for_input_issues(expression)

        processed = []
        i = 0
        n = len(expression)

        while i < n:
            ch = expression[i]
            nxt = expression[i + 1] if i + 1 < n else ""

            if ch == "^":
                processed.append("**")
            elif ch.isdigit() and nxt.isalpha():
                processed.append(ch)
                processed.append("*")
            elif ch == ")" and nxt == "(":
                processed.append(")*")
            elif ch in "+-*/" and nxt in "*/":
                raise MalformedSyntaxError(
                    f"Consecutive operators at position {i}: '{ch}{nxt}'",
                    user_message=f"Invalid operators near position {i + 1} ('{ch}{nxt}').",
                )
            else:
                processed.append(ch)
            i += 1

        cleaned = "".join(processed)
        expr = _sympify_safe(cleaned, expression)
        _ensure_algebraically_defined(expr)
        return expr

    def normalize(self, expr: Expr) -> Expr: # cannonical form of the expression ;
        def _pipeline(e: Expr) -> Expr:
            normalized = expand(e)
            for sym in normalized.free_symbols:
                normalized = collect(normalized, sym)
            # collect() can factor polynomials (e.g. 7x^2+x → x*(7x+1)), which
            # breaks structural term/coefficient comparison — re-expand to sum form.
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
        student_expr = self.normalize(self.parser(student_str))
        expected_expr = self.normalize(self.parser(expected_str))

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
        dropping a monomial — not a missing-term distribution mistake."""
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
    try:
        result = _validator.validate(data.step, data.expected)
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=data.expected,
            **result,
        )
    except MathInputError as exc:
        logger.info("Input rejected [%s]: %s", exc.category, exc)
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=data.expected,
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
            expected_step=data.expected,
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
        hint = f"{hint} — Solution: {session.expected_final}"

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
def create_problem(data: ProblemCreateRequest, db: OrmSession = Depends(get_db)):
    """
    Insert a new problem into the library (admin use; no auth yet).

    Body: ProblemCreateRequest with id, expression, expected_final, optional
    difficulty and topic.
    Returns: HTTP 201 with ProblemResponse on success.
    Raises HTTP 409 if the ID already exists, HTTP 500 on unexpected DB errors.
    """
    # TODO Phase 9+: restrict to admin role
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
def start_session(data: StartSessionRequest, db: OrmSession = Depends(get_db)):
    expr_provided = data.problem_expression is not None
    final_provided = data.expected_final is not None

    if expr_provided != final_provided:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Provide both expression and expected_final together, or "
                "neither (to use a pre-existing problem by ID)."
            },
        )

    try:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        if expr_provided and final_provided:
            if not data.problem_expression.strip() or not data.expected_final.strip():
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "expression and expected_final must be non-empty strings."
                    },
                )
            problem_expression = data.problem_expression
            expected_final = data.expected_final
            stmt = (
                insert(Problem)
                .values(
                    id=data.problem_id,
                    expression=problem_expression,
                    expected_final=expected_final,
                )
                .on_conflict_do_nothing()
            )
            db.execute(stmt)
        else:
            problem_row = db.query(Problem).filter_by(id=data.problem_id).first()
            if problem_row is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Problem not found. Provide expression and expected_final, "
                        "or use GET /sample-problem to find a valid problem ID."
                    },
                )
            problem_expression = problem_row.expression
            expected_final = problem_row.expected_final

        db.add(
            TutoringSession(
                session_id=session_id,
                problem_id=data.problem_id,
                attempt_count=0,
                incorrect_attempt_count=0,
                hint_level=1,
                created_at=now,
                last_active=now,
            )
        )
        db.commit()

        return StartSessionResponse(
            session_id=session_id,
            problem_id=data.problem_id,
            problem_expression=problem_expression,
            expected_final=expected_final,
            message="Session started.",
        )
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to start session")
        return StartSessionResponse(
            session_id="",
            problem_id=data.problem_id,
            problem_expression=data.problem_expression or "",
            expected_final=data.expected_final or "",
            message="Something went wrong while starting the session. Please try again.",
        )


@app.post("/submit-step", response_model=StepResult)
def submit_step(data: StepInput, db: OrmSession = Depends(get_db)):
    session_row = (
        db.query(TutoringSession).filter_by(session_id=data.session_id).first()
    )
    if session_row is None:
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=data.expected,
            is_equivalent=False,
            structural_diff=None,
            error_classification=None,
            hint="Session not found. Please start a new session.",
        )

    problem_row = db.query(Problem).filter_by(id=session_row.problem_id).first()
    if problem_row is None:
        return StepResult(
            session_id=data.session_id,
            received_step=data.step,
            expected_step=data.expected,
            is_equivalent=False,
            structural_diff=None,
            error_classification=None,
            hint="Session not found. Please start a new session.",
        )

    result = _handle_step_validation(data)

    session_obj = SessionState(
        session_id=session_row.session_id,
        problem_id=session_row.problem_id,
        problem_expression=problem_row.expression,
        expected_final=problem_row.expected_final,
        attempt_count=session_row.attempt_count + 1,
        incorrect_attempt_count=session_row.incorrect_attempt_count
        + (0 if result.is_equivalent else 1),
        hint_level=session_row.hint_level,
        attempt_history=[],
    )
    result = _apply_session_hint_policy(session_obj, result)

    session_row.attempt_count = session_obj.attempt_count
    session_row.incorrect_attempt_count = session_obj.incorrect_attempt_count
    session_row.hint_level = session_obj.hint_level
    session_row.last_active = datetime.utcnow()

    attempt_ts = datetime.utcnow()
    db.add(
        Attempt(
            session_id=session_row.session_id,
            step=data.step,
            expected=data.expected,
            is_equivalent=result.is_equivalent,
            error_type=(
                result.error_classification.get("error_type")
                if result.error_classification
                else None
            ),
            hint=result.hint,
            timestamp=attempt_ts,
        )
    )
    db.commit()

    return result


@app.get("/session/{session_id}")
def get_session(session_id: str, db: OrmSession = Depends(get_db)):
    session_row = (
        db.query(TutoringSession).filter_by(session_id=session_id).first()
    )
    if session_row is None:
        return {"error": "Session not found"}

    problem_row = db.query(Problem).filter_by(id=session_row.problem_id).first()
    problem_expression = problem_row.expression if problem_row else ""

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
        attempt_history=attempt_history,
        created_at=session_row.created_at,
        last_active=session_row.last_active,
    )


@app.delete("/session/{session_id}")
def delete_session(session_id: str, db: OrmSession = Depends(get_db)):
    session_row = (
        db.query(TutoringSession).filter_by(session_id=session_id).first()
    )
    if session_row is None:
        return {"deleted": False, "error": "Session not found"}

    db.query(Attempt).filter_by(session_id=session_id).delete()
    db.delete(session_row)
    db.commit()
    return {"deleted": True}


@app.get("/health")
def health():
    """Liveness probe — no database check."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness probe — verifies database connectivity."""
    if not check_db_connection():
        raise HTTPException(
            status_code=503,
            detail={"status": "unavailable", "db": "disconnected"},
        )
    return {"status": "ok", "db": "connected"}


@app.get("/")
def root():
    return {"status": "MathAssistant backend is running!", "version": "0.2.1"}
