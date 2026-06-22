"""Labeled evaluation benchmark for MathAssistant (72 problems).

Each entry includes the problem expression, correct step, metadata, and
canonical wrong answers with expected error types for the classifier.

Expressions use ^ (not **), matching StepValidator.parser().

v0.3 adds multi-hop problems (distribute-then-combine, FOIL-then-combine)
whose ``correct_step`` is the fully simplified final answer.
"""

from __future__ import annotations


def wrong(wrong_step: str, expected_error_type: str, description: str) -> dict:
    return {
        "wrong_step": wrong_step,
        "expected_error_type": expected_error_type,
        "description": description,
    }


def entry(
    problem_id: str,
    expression: str,
    correct_step: str,
    difficulty: str,
    topic: str,
    wrong_answers: list[dict],
) -> dict:
    return {
        "problem_id": problem_id,
        "expression": expression,
        "correct_step": correct_step,
        "difficulty": difficulty,
        "topic": topic,
        "wrong_answers": wrong_answers,
    }


EVALUATION_DATASET: list[dict] = [
    # ── DISTRIBUTION (20) ──────────────────────────────────────────────
    entry(
        "dist_001",
        "2(x+3)",
        "2x+6",
        "easy",
        "distribution",
        [
            wrong("6", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("2x+9", "arithmetic_error", "Distributed to x correctly but multiplied 3 by 3 instead of 2."),
        ],
    ),
    entry(
        "dist_002",
        "3(x-4)",
        "3x-12",
        "easy",
        "distribution",
        [
            wrong("-12", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("3x-8", "arithmetic_error", "Distributed to x correctly but multiplied -4 by 2 instead of 3."),
        ],
    ),
    entry(
        "dist_003",
        "4(2x+5)",
        "8x+20",
        "medium",
        "distribution",
        [
            wrong("20", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("8x+16", "arithmetic_error", "Distributed to x correctly but multiplied 5 by 4 instead of 5."),
        ],
    ),
    entry(
        "dist_004",
        "2(3x^2+x+1)",
        "6x^2+2x+2",
        "medium",
        "distribution",
        [
            wrong("6x^2+2x", "distribution_error", "Distributed to x terms but forgot the constant term."),
            wrong("6x^2+2x+1", "arithmetic_error", "Distributed to all terms but multiplied the constant by 1 instead of 2."),
        ],
    ),
    entry(
        "dist_005",
        "3(2x+4)",
        "6x+12",
        "easy",
        "distribution",
        [
            wrong("12", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("6x+9", "arithmetic_error", "Distributed to x correctly but multiplied 4 by 2 instead of 3."),
        ],
    ),
    entry(
        "dist_006",
        "5(x-3)",
        "5x-15",
        "easy",
        "distribution",
        [
            wrong("-15", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("5x-10", "arithmetic_error", "Distributed to x correctly but multiplied -3 by 3 instead of 5."),
        ],
    ),
    entry(
        "dist_007",
        "2(4x+7)",
        "8x+14",
        "easy",
        "distribution",
        [
            wrong("14", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("8x+10", "arithmetic_error", "Distributed to x correctly but multiplied 7 by 5 instead of 2."),
        ],
    ),
    entry(
        "dist_008",
        "6(x+2)",
        "6x+12",
        "easy",
        "distribution",
        [
            wrong("12", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("6x+8", "arithmetic_error", "Distributed to x correctly but multiplied 2 by 4 instead of 6."),
        ],
    ),
    entry(
        "dist_009",
        "4(3x-5)",
        "12x-20",
        "medium",
        "distribution",
        [
            wrong("-20", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("12x-16", "arithmetic_error", "Distributed to x correctly but multiplied -5 by 4 instead of 5."),
        ],
    ),
    entry(
        "dist_010",
        "3(x^2+2x+1)",
        "3x^2+6x+3",
        "medium",
        "distribution",
        [
            wrong("3x^2+6x", "distribution_error", "Distributed to x terms but forgot the constant term."),
            wrong("3x^2+6x+2", "arithmetic_error", "Distributed to all terms but multiplied the constant by 2 instead of 3."),
        ],
    ),
    entry(
        "dist_011",
        "2(5x^2-x+3)",
        "10x^2-2x+6",
        "hard",
        "distribution",
        [
            wrong("10x^2-2x", "distribution_error", "Distributed to x terms but forgot the constant term."),
            wrong("10x^2-2x+4", "arithmetic_error", "Distributed to all terms but multiplied the constant by 2 instead of 3."),
        ],
    ),
    entry(
        "dist_012",
        "7(x-4)",
        "7x-28",
        "easy",
        "distribution",
        [
            wrong("-28", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("7x-21", "arithmetic_error", "Distributed to x correctly but multiplied -4 by 6 instead of 7."),
        ],
    ),
    entry(
        "dist_013",
        "-2(x+5)",
        "-2x-10",
        "medium",
        "distribution",
        [
            wrong("-10", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("-2x-8", "arithmetic_error", "Distributed to x correctly but multiplied 5 by 2 instead of -2."),
        ],
    ),
    entry(
        "dist_014",
        "5(2x-3)",
        "10x-15",
        "medium",
        "distribution",
        [
            wrong("-15", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("10x-10", "arithmetic_error", "Distributed to x correctly but multiplied -3 by 3 instead of 5."),
        ],
    ),
    entry(
        "dist_015",
        "3(x^2-4)",
        "3x^2-12",
        "medium",
        "distribution",
        [
            wrong("-12", "distribution_error", "Multiplied only the constant; dropped the x^2 term."),
            wrong("3x^2-8", "arithmetic_error", "Distributed to all terms but multiplied -4 by 2 instead of 3."),
        ],
    ),
    entry(
        "dist_016",
        "4(x^2+3x-2)",
        "4x^2+12x-8",
        "hard",
        "distribution",
        [
            wrong("4x^2+12x", "distribution_error", "Distributed to x terms but forgot the constant term."),
            wrong("4x^2+12x-4", "arithmetic_error", "Distributed to all terms but multiplied -2 by 2 instead of 4."),
        ],
    ),
    entry(
        "dist_017",
        "2(3x^2+2x-1)",
        "6x^2+4x-2",
        "hard",
        "distribution",
        [
            wrong("6x^2+4x", "distribution_error", "Distributed to x terms but forgot the constant term."),
            wrong("6x^2+4x-4", "arithmetic_error", "Distributed to all terms but multiplied -1 by 4 instead of 2."),
        ],
    ),
    entry(
        "dist_018",
        "10(x+1)",
        "10x+10",
        "easy",
        "distribution",
        [
            wrong("10", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("10x+5", "arithmetic_error", "Distributed to x correctly but multiplied 1 by 5 instead of 10."),
        ],
    ),
    entry(
        "dist_019",
        "-3(2x-1)",
        "3-6x",
        "medium",
        "distribution",
        [
            wrong("3", "distribution_error", "Multiplied only the constant; dropped the x term."),
            wrong("-6x+6", "arithmetic_error", "Distributed to x correctly but multiplied -1 by -6 instead of -3."),
        ],
    ),
    entry(
        "dist_020",
        "5(x^2+x-3)",
        "5x^2+5x-15",
        "hard",
        "distribution",
        [
            wrong("5x^2+5x", "distribution_error", "Distributed to x terms but forgot the constant term."),
            wrong("5x^2+5x-10", "arithmetic_error", "Distributed to all terms but multiplied -3 by 3 instead of 5."),
        ],
    ),
    # ── SIMPLIFICATION (20) ────────────────────────────────────────────
    entry(
        "sign_001",
        "x+3-2x+1",
        "4-x",
        "easy",
        "simplification",
        [
            wrong("x+4", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("-2x+4", "arithmetic_error", "Correct sign on x but combined x terms to -2x instead of -x."),
        ],
    ),
    entry(
        "sign_002",
        "5x-3-7x+2",
        "-2x-1",
        "easy",
        "simplification",
        [
            wrong("2x-1", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("-4x-1", "arithmetic_error", "Correct sign on x but combined x terms to -4x instead of -2x."),
        ],
    ),
    entry(
        "sign_003",
        "-(x+4)+2x",
        "x-4",
        "medium",
        "simplification",
        [
            wrong("-x-4", "sign_error", "Flipped the sign when distributing the negative."),
            wrong("2x-4", "arithmetic_error", "Did not distribute the negative; kept +4 instead of -4."),
        ],
    ),
    entry(
        "arith_001",
        "3x+2x",
        "5x",
        "easy",
        "simplification",
        [
            wrong("-5x", "sign_error", "Flipped the sign when combining like terms."),
            wrong("6x", "arithmetic_error", "Correct sign but added coefficients to 6 instead of 5."),
        ],
    ),
    entry(
        "arith_002",
        "4x^2+3x^2-x",
        "7x^2-x",
        "medium",
        "simplification",
        [
            wrong("7x^2+x", "sign_error", "Flipped the sign on the x term when combining."),
            wrong("6x^2-x", "arithmetic_error", "Correct signs but combined x^2 coefficients to 6 instead of 7."),
        ],
    ),
    entry(
        "arith_003",
        "2x+3+4x-1",
        "6x+2",
        "easy",
        "simplification",
        [
            wrong("-6x+2", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("4x+2", "arithmetic_error", "Correct sign but combined x terms to 4x instead of 6x."),
        ],
    ),
    entry(
        "simp_001",
        "2x+5x-3",
        "7x-3",
        "easy",
        "simplification",
        [
            wrong("-7x-3", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("6x-3", "arithmetic_error", "Correct sign but combined x terms to 6x instead of 7x."),
        ],
    ),
    entry(
        "simp_002",
        "4x-x+6",
        "3x+6",
        "easy",
        "simplification",
        [
            wrong("-3x+6", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("2x+6", "arithmetic_error", "Correct sign but combined x terms to 2x instead of 3x."),
        ],
    ),
    entry(
        "simp_003",
        "3x+2-x+5",
        "2x+7",
        "medium",
        "simplification",
        [
            wrong("-2x+7", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("3x+7", "arithmetic_error", "Correct sign but combined x terms to 3x instead of 2x."),
        ],
    ),
    entry(
        "simp_004",
        "6x-4x-2x+1",
        "1",
        "medium",
        "simplification",
        [
            wrong("-1", "sign_error", "Flipped the sign on the constant result."),
            wrong("2", "arithmetic_error", "Correct sign but wrong constant value after combining."),
        ],
    ),
    entry(
        "simp_005",
        "x+x+x",
        "3x",
        "easy",
        "simplification",
        [
            wrong("-3x", "sign_error", "Flipped the sign when combining like terms."),
            wrong("2x", "arithmetic_error", "Correct sign but counted three x terms as 2x."),
        ],
    ),
    entry(
        "simp_006",
        "-2x+4x-1",
        "2x-1",
        "medium",
        "simplification",
        [
            wrong("-2x-1", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("3x-1", "arithmetic_error", "Correct sign but combined x terms to 3x instead of 2x."),
        ],
    ),
    entry(
        "simp_007",
        "3x^2+x-x^2+2",
        "2x^2+x+2",
        "medium",
        "simplification",
        [
            wrong("-2x^2+x+2", "sign_error", "Flipped the sign on the x^2 term when combining."),
            wrong("3x^2+x+2", "arithmetic_error", "Correct signs but combined x^2 terms to 3x^2 instead of 2x^2."),
        ],
    ),
    entry(
        "simp_008",
        "8x-3x+4-2",
        "5x+2",
        "hard",
        "simplification",
        [
            wrong("-5x+2", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("4x+2", "arithmetic_error", "Correct sign but combined x terms to 4x instead of 5x."),
        ],
    ),
    entry(
        "simp_009",
        "5x+2x-4x+3",
        "3x+3",
        "medium",
        "simplification",
        [
            wrong("-3x+3", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("2x+3", "arithmetic_error", "Correct sign but combined x terms to 2x instead of 3x."),
        ],
    ),
    entry(
        "simp_010",
        "-x+3x-2",
        "2x-2",
        "hard",
        "simplification",
        [
            wrong("-2x-2", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("3x-2", "arithmetic_error", "Correct sign but combined x terms to 3x instead of 2x."),
        ],
    ),
    entry(
        "simp_011",
        "2x^2+3x^2-5",
        "5x^2-5",
        "medium",
        "simplification",
        [
            wrong("-5x^2-5", "sign_error", "Flipped the sign when combining the x^2 terms."),
            wrong("4x^2-5", "arithmetic_error", "Correct sign but combined x^2 terms to 4x^2 instead of 5x^2."),
        ],
    ),
    entry(
        "simp_012",
        "7x-2x+3x-1",
        "8x-1",
        "hard",
        "simplification",
        [
            wrong("-8x-1", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("7x-1", "arithmetic_error", "Correct sign but combined x terms to 7x instead of 8x."),
        ],
    ),
    entry(
        "simp_013",
        "x-5x+8",
        "8-4x",
        "hard",
        "simplification",
        [
            wrong("4x+8", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("-3x+8", "arithmetic_error", "Correct sign but combined x terms to -3x instead of -4x."),
        ],
    ),
    entry(
        "simp_014",
        "4x+3-2x+1",
        "2x+4",
        "hard",
        "simplification",
        [
            wrong("-2x+4", "sign_error", "Flipped the sign when combining the x terms."),
            wrong("3x+4", "arithmetic_error", "Correct sign but combined x terms to 3x instead of 2x."),
        ],
    ),
    # ── DOUBLE EXPANSION (10) ────────────────────────────────────────
    entry(
        "dexp_001",
        "(x+2)(x+3)",
        "x^2+5x+6",
        "easy",
        "double_expansion",
        [
            wrong("x^2+6", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("x^2+4x+6", "arithmetic_error", "Included all terms but added middle coefficients to 4x instead of 5x."),
        ],
    ),
    entry(
        "dexp_002",
        "(x+1)(x+4)",
        "x^2+5x+4",
        "easy",
        "double_expansion",
        [
            wrong("x^2+4", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("x^2+3x+4", "arithmetic_error", "Included all terms but added middle coefficients to 3x instead of 5x."),
        ],
    ),
    entry(
        "dexp_003",
        "(x-2)(x+3)",
        "x^2+x-6",
        "medium",
        "double_expansion",
        [
            wrong("x^2-6", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("x^2+2x-6", "arithmetic_error", "Included all terms but added middle coefficients to 2x instead of x."),
        ],
    ),
    entry(
        "dexp_004",
        "(x+5)(x-1)",
        "x^2+4x-5",
        "medium",
        "double_expansion",
        [
            wrong("x^2-5", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("x^2+2x-5", "arithmetic_error", "Included all terms but added middle coefficients to 2x instead of 4x."),
        ],
    ),
    entry(
        "dexp_005",
        "(2x+1)(x+3)",
        "2x^2+7x+3",
        "medium",
        "double_expansion",
        [
            wrong("2x^2+3", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("2x^2+5x+3", "arithmetic_error", "Included all terms but added middle coefficients to 5x instead of 7x."),
        ],
    ),
    entry(
        "dexp_006",
        "(x+2)(x-2)",
        "x^2-4",
        "easy",
        "double_expansion",
        [
            wrong("-4", "distribution_error", "Multiplied only the outer terms; dropped the x^2 term."),
            wrong("x^2-2", "arithmetic_error", "Included x^2 and constant but wrong constant value."),
        ],
    ),
    entry(
        "dexp_007",
        "(x+3)^2",
        "x^2+6x+9",
        "hard",
        "double_expansion",
        [
            wrong("x^2+9", "distribution_error", "Squared the first and last terms only; dropped the middle term."),
            wrong("x^2+4x+9", "arithmetic_error", "Included all terms but doubled the middle coefficient incorrectly."),
        ],
    ),
    entry(
        "dexp_008",
        "(2x+3)(x-1)",
        "2x^2+x-3",
        "hard",
        "double_expansion",
        [
            wrong("2x^2-3", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("2x^2+2x-3", "arithmetic_error", "Included all terms but added middle coefficients to 2x instead of x."),
        ],
    ),
    entry(
        "dexp_009",
        "(x-4)(x-1)",
        "x^2-5x+4",
        "hard",
        "double_expansion",
        [
            wrong("x^2+4", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("x^2-3x+4", "arithmetic_error", "Included all terms but added middle coefficients to -3x instead of -5x."),
        ],
    ),
    entry(
        "dexp_010",
        "(3x+2)(x+2)",
        "3x^2+8x+4",
        "medium",
        "double_expansion",
        [
            wrong("3x^2+4", "distribution_error", "Multiplied only the first and last terms; dropped the cross terms."),
            wrong("3x^2+6x+4", "arithmetic_error", "Included all terms but added middle coefficients to 6x instead of 8x."),
        ],
    ),
    # ── LINEAR STEPS (10) ────────────────────────────────────────────
    entry(
        "lin_001",
        "3x-x+4",
        "2x+4",
        "easy",
        "linear_steps",
        [
            wrong("-2x+4", "sign_error", "Flipped the sign when combining x terms toward isolation."),
            wrong("4x+4", "arithmetic_error", "Correct sign but combined x terms to 4x instead of 2x."),
        ],
    ),
    entry(
        "lin_002",
        "5x+3-2x",
        "3x+3",
        "easy",
        "linear_steps",
        [
            wrong("-3x+3", "sign_error", "Flipped the sign when combining x terms toward isolation."),
            wrong("5x+3", "arithmetic_error", "Did not combine -2x; left x terms uncombined."),
        ],
    ),
    entry(
        "lin_003",
        "4x-3x+7",
        "x+7",
        "medium",
        "linear_steps",
        [
            wrong("-x+7", "sign_error", "Flipped the sign when combining x terms toward isolation."),
            wrong("2x+7", "arithmetic_error", "Correct sign but combined x terms to 2x instead of x."),
        ],
    ),
    entry(
        "lin_004",
        "2x+8-x-3",
        "x+5",
        "medium",
        "linear_steps",
        [
            wrong("-x+5", "sign_error", "Flipped the sign when combining x terms toward isolation."),
            wrong("2x+5", "arithmetic_error", "Correct sign but combined x terms to 2x instead of x."),
        ],
    ),
    entry(
        "lin_005",
        "6x-2x+1-3",
        "4x-2",
        "medium",
        "linear_steps",
        [
            wrong("-4x-2", "sign_error", "Flipped the sign when combining x terms toward isolation."),
            wrong("6x-2", "arithmetic_error", "Did not fully combine x terms before simplifying constants."),
        ],
    ),
    entry(
        "lin_006",
        "x+2x-3x+5",
        "5",
        "hard",
        "linear_steps",
        [
            wrong("-5", "sign_error", "Flipped the sign on the constant after x terms canceled."),
            wrong("2", "arithmetic_error", "Correct sign but wrong constant after combining."),
        ],
    ),
    entry(
        "lin_007",
        "7x-5x-4+2",
        "2x-2",
        "hard",
        "linear_steps",
        [
            wrong("-2x-2", "sign_error", "Flipped the sign when combining x terms toward isolation."),
            wrong("4x-2", "arithmetic_error", "Correct sign but combined x terms to 4x instead of 2x."),
        ],
    ),
    entry(
        "lin_008",
        "3x+4-5x+6",
        "10-2x",
        "medium",
        "linear_steps",
        [
            wrong("2x+10", "sign_error", "Flipped the sign when combining x terms toward isolation."),
            wrong("-4x+10", "arithmetic_error", "Correct sign but combined x terms to -4x instead of -2x."),
        ],
    ),
    entry(
        "lin_009",
        "2x^2+x-x^2",
        "x^2+x",
        "medium",
        "linear_steps",
        [
            wrong("-x^2-x", "sign_error", "Flipped signs on both terms when combining x^2 terms."),
            wrong("2x^2+2x", "arithmetic_error", "Did not combine x^2 terms correctly."),
        ],
    ),
    entry(
        "lin_010",
        "4x^2-x^2+3x",
        "3x^2+3x",
        "hard",
        "linear_steps",
        [
            wrong("-3x^2-3x", "sign_error", "Flipped signs on both terms when combining."),
            wrong("2x^2+2x", "arithmetic_error", "Wrong x^2 coefficient after combining like terms."),
        ],
    ),
    # ── MULTI-HOP (12) ───────────────────────────────────────────────
    entry(
        "mhop_001",
        "2(x+3)+4",
        "2x+10",
        "easy",
        "multihop",
        [
            wrong("6+4", "distribution_error", "Combined constants only; dropped the distributed x term."),
            wrong("2x+12", "arithmetic_error", "Distributed correctly but added 6+4 to 12 instead of 10."),
        ],
    ),
    entry(
        "mhop_002",
        "3(x-2)+5",
        "3x-1",
        "easy",
        "multihop",
        [
            wrong("-1", "distribution_error", "Used only the trailing constant; dropped the x term."),
            wrong("3x-2", "arithmetic_error", "Distributed correctly but combined -6+5 to -2 instead of -1."),
        ],
    ),
    entry(
        "mhop_003",
        "-2(x+1)+3",
        "1-2x",
        "medium",
        "multihop",
        [
            wrong("-2x", "distribution_error", "Kept only the variable part after distribution."),
            wrong("-2x+3", "arithmetic_error", "Distributed correctly but combined -2+3 to 3 on the constant line."),
        ],
    ),
    entry(
        "mhop_004",
        "4(2x+1)+2",
        "8x+6",
        "medium",
        "multihop",
        [
            wrong("8x", "distribution_error", "Dropped the constant terms after distributing."),
            wrong("8x+5", "arithmetic_error", "Distributed correctly but combined 4+2 to 5 instead of 6."),
        ],
    ),
    entry(
        "mhop_005",
        "5(x+2)-3",
        "5x+7",
        "medium",
        "multihop",
        [
            wrong("5x", "distribution_error", "Dropped constants after distributing 5(x+2)."),
            wrong("5x+8", "arithmetic_error", "Distributed correctly but combined 10-3 to 8 instead of 7."),
        ],
    ),
    entry(
        "mhop_006",
        "(x+1)(x+2)+3",
        "x^2+3x+5",
        "medium",
        "multihop",
        [
            wrong("x^2+5", "distribution_error", "FOIL expansion missing the middle x terms."),
            wrong("x^2+3x+6", "arithmetic_error", "Expanded correctly but added trailing 3 to get 6 instead of 5."),
        ],
    ),
    entry(
        "mhop_007",
        "(x+2)(x-1)+4",
        "x^2+x+2",
        "medium",
        "multihop",
        [
            wrong("x^2+x", "distribution_error", "Expanded the product but dropped the trailing constant work."),
            wrong("x^2+x+3", "arithmetic_error", "Expanded correctly but combined -2+4 to 3 instead of 2."),
        ],
    ),
    entry(
        "mhop_008",
        "(2x+1)(x+3)+2",
        "2x^2+7x+5",
        "hard",
        "multihop",
        [
            wrong("2x^2+7x", "distribution_error", "Expanded the product but omitted constant terms."),
            wrong("2x^2+7x+4", "arithmetic_error", "Expanded correctly but combined 3+2 to 4 instead of 5."),
        ],
    ),
    entry(
        "mhop_009",
        "2(x+5)+3(x-1)",
        "5x+7",
        "hard",
        "multihop",
        [
            wrong("5x", "distribution_error", "Combined x terms but dropped all constants."),
            wrong("5x+8", "arithmetic_error", "Distributed both factors but combined 10-3 to 8 instead of 7."),
        ],
    ),
    entry(
        "mhop_010",
        "(x-2)(x+5)+1",
        "x^2+3x-9",
        "hard",
        "multihop",
        [
            wrong("x^2+3x", "distribution_error", "Expanded the product but dropped constant terms."),
            wrong("x^2+3x-8", "arithmetic_error", "Expanded correctly but combined -10+1 to -8 instead of -9."),
        ],
    ),
    entry(
        "mhop_011",
        "3(2x-1)+4",
        "6x+1",
        "medium",
        "multihop",
        [
            wrong("6x", "distribution_error", "Distributed to the x term but dropped constants."),
            wrong("6x+2", "arithmetic_error", "Distributed correctly but combined -3+4 to 2 instead of 1."),
        ],
    ),
    entry(
        "mhop_012",
        "(8x+6x^2+2)(8x^2+22x+19)",
        "48x^4+196x^3+306x^2+196x+38",
        "hard",
        "multihop",
        [
            wrong("48x^4+38", "distribution_error", "Multiplied only outer terms; dropped cross terms."),
            wrong(
                "48x^4+196x^3+300x^2+196x+38",
                "arithmetic_error",
                "Distributed all terms but combined like x^2 coefficients to 300 instead of 306.",
            ),
        ],
    ),
]


FLAT_DATASET: list[dict] = [
    {
        "problem_id": problem["problem_id"],
        "expression": problem["expression"],
        "correct_step": problem["correct_step"],
        "wrong_step": wrong_entry["wrong_step"],
        "expected_error_type": wrong_entry["expected_error_type"],
    }
    for problem in EVALUATION_DATASET
    for wrong_entry in problem["wrong_answers"]
]
