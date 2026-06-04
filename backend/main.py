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
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sympy import (
    Add, Mul, Pow, Symbol,
    expand, collect, simplify, sympify, E,
)
from sympy.core.expr import Expr

# ──────────────────────────────────────────────────────────────────────────────
# App bootstrap
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="MathAssistant", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", # what do each of these urls(? can we even call them URLs?) mean?
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# Request / response models
# ──────────────────────────────────────────────────────────────────────────────
class StepInput(BaseModel):
    session_id: str
    step: str       # student's expression, e.g. "2*x + 4" or "x^2 + 5*x + 6"
    expected: str   # correct expression,  e.g. "2*x + 6" or "x^2 + 5*x + 6"


class StepResult(BaseModel):
    session_id: str
    received_step: str
    expected_step: str
    is_equivalent: bool
    structural_diff: dict | None
    error_classification: dict | None
    hint: str


# ──────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────────────────────────────────────
class ParseError(ValueError):
    """Raised when a math string cannot be parsed into a SymPy expression."""


# ══════════════════════════════════════════════════════════════════════════════
# HINT ENGINE
# A simple lookup table kept outside StepValidator because it is stateless
# and may be extended / swapped without touching the validation logic.
# ══════════════════════════════════════════════════════════════════════════════
_HINT_MAP: dict[str, str] = {
    "sign_error":         "Check your negative signs carefully.",
    "arithmetic_error":   "Double-check your arithmetic calculations.",
    "distribution_error": "Make sure you distribute multiplication across all terms.",
    "unknown":            "Review each step carefully and check your work.",
}


def generate_hint(error_type: str) -> str:
    """Return a student-facing hint string for a given error type."""
    return _HINT_MAP.get(error_type, _HINT_MAP["unknown"])


# ══════════════════════════════════════════════════════════════════════════════
# STEP VALIDATOR
# Encapsulates all four validation layers in one coherent class.
# ══════════════════════════════════════════════════════════════════════════════
class StepValidator:

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 1 – PARSING
    # ──────────────────────────────────────────────────────────────────────────
    def parser(self, expression: str) -> Expr:
        """
        Pre-process a raw math string, then hand it to SymPy's sympify.

        Exponent notation: use ^ only (e.g. x^2, (x+1)^2). Python's ** is
        rejected in user input; ^ is converted to ** internally for SymPy.

        Transformations applied (left-to-right, single pass):
          • digit immediately followed by a letter  →  insert implicit '*'
            e.g. "2x"  →  "2*x",   "3xy" → "3*x*y" (handled symbol by symbol)
          • '^'  →  '**'   (internal only, for sympify)
          • closing ')' immediately followed by '('  →  insert '*'
            e.g. "(x+1)(x+2)" → "(x+1)*(x+2)"

        Raises ParseError on consecutive binary operators or sympify failure.
        """
        if "**" in expression:
            raise ParseError(
                "Use ^ for exponents (e.g. x^2), not **"
            )

        processed = []
        i = 0
        n = len(expression)

        while i < n:
            ch = expression[i]
            nxt = expression[i + 1] if i + 1 < n else ""

            # Caret exponent → Python exponent for sympify (user never types **)
            if ch == "^":
                processed.append("**")

            # Implicit multiplication: digit → letter  (e.g. 2x → 2*x)
            elif ch.isdigit() and nxt.isalpha():
                processed.append(ch)
                processed.append("*")

            # Implicit multiplication: ) → (  (e.g. (a+b)(c+d) → (a+b)*(c+d))
            elif ch == ")" and nxt == "(":
                processed.append(")*")

            # Guard against consecutive binary operators in user input (e.g. "+-", "*/")
            elif ch in "+-*/" and nxt in "*/":
                # Note: "+- " or " -" (unary minus) is intentionally allowed
                raise ParseError(
                    f"Consecutive operators at position {i}: '{ch}{nxt}'"
                )

            else:
                processed.append(ch)

            i += 1

        cleaned = "".join(processed)

        try:
            # Pass {'e': E} so that bare 'e' is Euler's number, not a symbol
            return sympify(cleaned, locals={"e": E})
        except Exception as exc:
            raise ParseError(f"Cannot parse '{expression}': {exc}") from exc

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 2 – NORMALIZATION
    # ──────────────────────────────────────────────────────────────────────────
    def normalize(self, expr: Expr) -> Expr:
        """
        Canonicalize a SymPy expression for stable, order-independent comparison.

        Pipeline:
          expand   – distribute multiplications, remove brackets
          collect  – group terms by each free symbol
          simplify – apply algebraic simplification rules
        """
        normalized = expand(expr)
        for sym in normalized.free_symbols:
            normalized = collect(normalized, sym)
        return simplify(normalized)

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 3 – COMPARISON  (structural diff extraction lives here)
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _get_terms(expr: Expr) -> set:
        """
        Return the top-level additive terms of an expression.

        For an Add node  (a + b + c) → {a, b, c}
        For anything else (single term)  → {expr}
        """
        return set(expr.args) if isinstance(expr, Add) else {expr}

    def _extract_structural_diff(
        self,
        student: Expr,
        expected: Expr,
    ) -> dict:
        """
        Inspect two normalized SymPy expressions and return a structured
        description of their differences.

        Returns
        -------
        {
          "top_level_op": {
              "student":  str   – SymPy class name of student's top node
              "expected": str   – SymPy class name of expected's top node
              "match":    bool
          },
          "term_diff": {
              "missing_terms": list[str]  – in expected but not in student
              "extra_terms":   list[str]  – in student but not in expected
          },
          "coeff_diff": {
              "<symbol>": {"student": str, "expected": str}, ...
          },
          "same_monomial_basis": bool  – True if both share the same coeff keys
        }
        """
        # ── Top-level operation type ──────────────────────────────────────────
        student_op  = type(student).__name__
        expected_op = type(expected).__name__

        # ── Term-level diff ───────────────────────────────────────────────────
        student_terms  = self._get_terms(student)
        expected_terms = self._get_terms(expected)

        missing_terms = [str(t) for t in expected_terms - student_terms]
        extra_terms   = [str(t) for t in student_terms  - expected_terms]

        # ── Coefficient-level diff ────────────────────────────────────────────
        # as_coefficients_dict() → {symbol_or_1: coefficient}
        # The key `1` holds the constant term.
        student_coeffs  = student.as_coefficients_dict()
        expected_coeffs = expected.as_coefficients_dict()

        all_keys = set(student_coeffs) | set(expected_coeffs)
        coeff_diff: dict[str, dict] = {}
        for key in all_keys:
            s_val = student_coeffs.get(key, 0)
            e_val = expected_coeffs.get(key, 0)
            if simplify(s_val - e_val) != 0:
                coeff_diff[str(key)] = {
                    "student":  str(s_val),
                    "expected": str(e_val),
                }

        same_monomial_basis = set(student_coeffs.keys()) == set(expected_coeffs.keys())

        return {
            "top_level_op": {
                "student":  student_op,
                "expected": expected_op,
                "match":    student_op == expected_op,
            },
            "term_diff": {
                "missing_terms": missing_terms,
                "extra_terms":   extra_terms,
            },
            "coeff_diff": coeff_diff,
            "same_monomial_basis": same_monomial_basis,
        }

    def comparison(self, student_str: str, expected_str: str) -> dict:
        """
        Full comparison pipeline for two raw expression strings.

        Steps
        -----
        1. parse(student_str)   → SymPy Expr
        2. parse(expected_str)  → SymPy Expr
        3. normalize both
        4. equivalence check:   simplify(student - expected) == 0
        5. structural diff:     _extract_structural_diff()

        Returns
        -------
        {
          "is_equivalent":  bool,
          "structural_diff": dict   (see _extract_structural_diff)
        }
        """
        student_expr  = self.normalize(self.parser(student_str))
        expected_expr = self.normalize(self.parser(expected_str))

        is_equivalent = simplify(student_expr - expected_expr) == 0
        structural_diff = self._extract_structural_diff(student_expr, expected_expr)

        return {
            "is_equivalent":  bool(is_equivalent),
            "structural_diff": structural_diff,
        }

    def _parse_internal(self, expr_str: str) -> Expr:
        """Parse SymPy string forms using the user-facing ^ exponent rules."""
        return self.parser(expr_str.replace("**", "^"))

    @staticmethod
    def _is_constant_only_term_noise(
        missing_terms: list[str],
        extra_terms: list[str],
    ) -> bool:
        """
        True when term-level missing/extra are only numeric constants
        (e.g. 3 vs -3), so coeff_diff rules should handle classification.
        """
        from sympy import sympify

        for term_str in missing_terms + extra_terms:
            try:
                if not sympify(term_str).is_Number:
                    return False
            except Exception:
                return False
        return bool(missing_terms or extra_terms)

    def _is_distribution_error(self, structural_diff: dict) -> bool:
        """
        Distribution applies only when whole terms are missing after expansion,
        not when the same monomial basis differs only by coefficients.
        """
        missing_terms = structural_diff["term_diff"]["missing_terms"]
        if not missing_terms:
            return False

        extra_terms = structural_diff["term_diff"]["extra_terms"]
        if self._is_constant_only_term_noise(missing_terms, extra_terms):
            return False

        if structural_diff.get("same_monomial_basis", False):
            return False

        return True

    # ──────────────────────────────────────────────────────────────────────────
    # LAYER 4 – CLASSIFICATION
    # ──────────────────────────────────────────────────────────────────────────
    def classify_error(self, structural_diff: dict) -> dict:
        """
        Map structural differences to an error type using deterministic rules
        evaluated in priority order.

        Priority
        --------
        1. distribution_error  – substantive terms missing after expansion
           (skipped when only constants differ or the monomial basis is unchanged)
           Rationale: if a student forgot to distribute, whole terms vanish.
           Catch this before checking coefficients, which would give a
           misleading arithmetic_error.

        2. sign_error          – all differing coefficients are sign-flips
           Rationale: s_coeff + e_coeff == 0  means same magnitude, opposite sign.

        3. arithmetic_error    – coefficients differ in magnitude
           Rationale: anything else that touches a coefficient is a calculation mistake.

        4. unknown             – fallback; should rarely be reached after a failed
           equivalence check, but provided for robustness.

        Returns
        -------
        {
          "error_type":  str         ("distribution_error" | "sign_error"
                                      | "arithmetic_error" | "unknown")
          "confidence":  str         ("high" | "medium" | "low")
          "reason":      str         human-readable explanation
        }
        """
        coeff_diff    = structural_diff.get("coeff_diff", {})
        missing_terms = structural_diff["term_diff"]["missing_terms"]
        extra_terms   = structural_diff["term_diff"]["extra_terms"]

        # ── Rule 1: Distribution error ────────────────────────────────────────
        if self._is_distribution_error(structural_diff):
            return {
                "error_type": "distribution_error",
                "confidence": "high",
                "reason": f"Terms missing after expansion: {missing_terms}",
            }

        # ── Rule 2: Sign error ────────────────────────────────────────────────
        # All differing coefficients satisfy  student_coeff + expected_coeff == 0,
        # i.e. equal magnitude but opposite sign.
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
                return {
                    "error_type": "sign_error",
                    "confidence": "high",
                    "reason": (
                        f"Sign is flipped for: {list(coeff_diff.keys())}"
                    ),
                }

        # ── Rule 3: Arithmetic error ──────────────────────────────────────────
        if coeff_diff:
            # Downgrade confidence to "medium" when extra spurious terms also exist
            confidence = "medium" if extra_terms else "high"
            return {
                "error_type": "arithmetic_error",
                "confidence": confidence,
                "reason": (
                    f"Coefficient mismatch for: {list(coeff_diff.keys())}"
                ),
            }

        # ── Rule 4: Fallback ──────────────────────────────────────────────────
        return {
            "error_type": "unknown",
            "confidence": "low",
            "reason": "Expressions differ but no specific error pattern was detected.",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # ORCHESTRATOR – full pipeline
    # ──────────────────────────────────────────────────────────────────────────
    def validate(self, student_str: str, expected_str: str) -> dict:
        """
        Orchestrates the complete pipeline:

          student_str
            → parse + normalize  (parser / normalize)
            → compare + diff     (comparison)
            → classify           (classify_error)      ← skipped if correct
            → hint               (generate_hint)       ← skipped if correct

        Returns a flat dict consumed directly by the API route.
        """
        comparison_result = self.comparison(student_str, expected_str)
        is_equivalent     = comparison_result["is_equivalent"]
        structural_diff   = comparison_result["structural_diff"]

        if is_equivalent:
            return {
                "is_equivalent":      True,
                "structural_diff":    structural_diff,
                "error_classification": None,
                "hint":               "Correct! Well done.",
            }

        error_classification = self.classify_error(structural_diff)
        hint                 = generate_hint(error_classification["error_type"])

        return {
            "is_equivalent":      False,
            "structural_diff":    structural_diff,
            "error_classification": error_classification,
            "hint":               hint,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton validator (avoids re-instantiation on every request)
# ──────────────────────────────────────────────────────────────────────────────
_validator = StepValidator()


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/submit-step", response_model=StepResult)
def submit_step(data: StepInput):
    try:
        result = _validator.validate(data.step, data.expected)
        return StepResult(
            session_id   = data.session_id,
            received_step= data.step,
            expected_step= data.expected,
            **result,
        )
    except ParseError as exc:
        return StepResult(
            session_id            = data.session_id,
            received_step         = data.step,
            expected_step         = data.expected,
            is_equivalent         = False,
            structural_diff       = None,
            error_classification  = None,
            hint                  = f"Could not parse expression: {exc}",
        )
    except Exception as exc:
        # Catch-all so the server never returns a 500 to the student
        return StepResult(
            session_id            = data.session_id,
            received_step         = data.step,
            expected_step         = data.expected,
            is_equivalent         = False,
            structural_diff       = None,
            error_classification  = None,
            hint                  = f"Unexpected error: {exc}",
        )


@app.get("/")
def root():
    return {"status": "MathAssistant backend is running!", "version": "0.2.0"}