"""Phase 4 — hint quality: specific focus, no answer leakage, graduated levels."""
from main import generate_hint


def test_hint_references_coefficient_focus_not_full_input():
    diff = {
        "term_diff": {"missing_terms": [], "extra_terms": []},
        "coeff_diff": {"x": {"student": "3", "expected": "6"}},
    }
    hint = generate_hint("arithmetic_error", structural_diff=diff, hint_level=1)
    assert "x" in hint.lower() or "term" in hint.lower()
    assert "6" not in hint
    assert "expected" not in hint.lower()


def test_distribution_hint_does_not_list_missing_terms():
    diff = {
        "term_diff": {"missing_terms": ["x^{2}"], "extra_terms": []},
        "coeff_diff": {},
    }
    hint = generate_hint("distribution_error", structural_diff=diff, hint_level=1)
    assert "x^{2}" not in hint
    assert "x^2" not in hint


def test_graduated_hints_differ_by_level():
    diff = {
        "term_diff": {"missing_terms": [], "extra_terms": []},
        "coeff_diff": {"1": {"student": "3", "expected": "-3"}},
    }
    h1 = generate_hint("sign_error", structural_diff=diff, hint_level=1)
    h2 = generate_hint("sign_error", structural_diff=diff, hint_level=2)
    assert h1 != h2


def test_validate_hint_on_wrong_step(validator):
    result = validator.validate("2*x+3", "2*x+6")
    assert result["is_equivalent"] is False
    assert "6" not in result["hint"]
    assert len(result["hint"]) > 10
