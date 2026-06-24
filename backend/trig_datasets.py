"""Training and testing datasets for trigonometry topics (20 problems each).

Each topic includes 10 problems: 3 easy, 3 medium, 4 hard.
"""

from __future__ import annotations

from trig_engine import try_build_trig_plan


def wrong(wrong_step: str, expected_error_type: str, description: str) -> dict:
    return {
        "wrong_step": wrong_step,
        "expected_error_type": expected_error_type,
        "description": description,
    }


def entry(
    problem_id: str,
    expression: str,
    difficulty: str,
    topic: str,
    wrong_answers: list[dict],
) -> dict:
    plan = try_build_trig_plan(expression)
    return {
        "problem_id": problem_id,
        "expression": expression,
        "correct_step": plan.final_answer,
        "difficulty": difficulty,
        "topic": topic,
        "wrong_answers": wrong_answers,
    }


CORE_TRIG_TRAINING = [
    entry("ctrig_tr_01", "sin(pi/2)", "easy", "core_trig", [
        wrong("0", "arithmetic_error", "Confused sine with cosine at pi/2."),
        wrong("pi/2", "unknown", "Returned the angle instead of evaluating sine."),
    ]),
    entry("ctrig_tr_02", "cos(0)", "easy", "core_trig", [
        wrong("0", "arithmetic_error", "Evaluated cosine at zero incorrectly."),
        wrong("-1", "sign_error", "Used the value of cos(pi) instead of cos(0)."),
    ]),
    entry("ctrig_tr_03", "tan(pi/4)", "easy", "core_trig", [
        wrong("0", "arithmetic_error", "Confused tangent with sine at pi/4."),
        wrong("sqrt(2)", "arithmetic_error", "Returned sin(pi/4)+cos(pi/4) instead of tan(pi/4)."),
    ]),
    entry("ctrig_tr_04", "sin(pi/6)+cos(pi/6)", "medium", "core_trig", [
        wrong("1", "arithmetic_error", "Added the two exact values incorrectly."),
        wrong("sqrt(3)", "arithmetic_error", "Evaluated only one of the two terms."),
    ]),
    entry("ctrig_tr_05", "sin(pi/4)*cos(pi/4)", "medium", "core_trig", [
        wrong("sqrt(2)", "arithmetic_error", "Added sine and cosine instead of multiplying."),
        wrong("1/4", "arithmetic_error", "Squared one factor but did not multiply both."),
    ]),
    entry("ctrig_tr_06", "tan(pi/6)+sin(pi/6)", "medium", "core_trig", [
        wrong("1", "arithmetic_error", "Rounded both terms to one before adding."),
        wrong("sqrt(3)/2", "arithmetic_error", "Evaluated tangent but omitted sine."),
    ]),
    entry("ctrig_tr_07", "2*sin(pi/6)*cos(pi/3)+tan(pi/4)", "hard", "core_trig", [
        wrong("1", "arithmetic_error", "Dropped the tangent term after multiplying."),
        wrong("2", "arithmetic_error", "Multiplied coefficients but ignored one factor."),
    ]),
    entry("ctrig_tr_08", "sin(pi/3)-cos(pi/6)+tan(pi/4)", "hard", "core_trig", [
        wrong("0", "sign_error", "Subtracted cosine with the wrong sign."),
        wrong("2", "arithmetic_error", "Evaluated sine and tangent but ignored cosine."),
    ]),
    entry("ctrig_tr_09", "3*sin(pi/2)-2*cos(0)+tan(pi/4)", "hard", "core_trig", [
        wrong("1", "arithmetic_error", "Computed 3-2 but forgot the tangent term."),
        wrong("4", "arithmetic_error", "Added all terms instead of subtracting cosine."),
    ]),
    entry("ctrig_tr_10", "2*sin(pi/4)*cos(pi/4)+tan(pi/6)", "hard", "core_trig", [
        wrong("1", "arithmetic_error", "Evaluated the product but omitted tangent."),
        wrong("sqrt(3)", "arithmetic_error", "Returned tangent only and ignored the product."),
    ]),
]

CORE_TRIG_TESTING = [
    entry("ctrig_ts_01", "sin(pi/6)", "easy", "core_trig", [
        wrong("sqrt(3)/2", "arithmetic_error", "Returned the cosine value at pi/6."),
        wrong("1", "arithmetic_error", "Confused pi/6 with pi/2."),
    ]),
    entry("ctrig_ts_02", "cos(pi/3)", "easy", "core_trig", [
        wrong("sqrt(3)/2", "arithmetic_error", "Returned cosine of pi/6 instead of pi/3."),
        wrong("0", "arithmetic_error", "Confused cosine with sine at pi/3."),
    ]),
    entry("ctrig_ts_03", "tan(pi/3)", "easy", "core_trig", [
        wrong("1", "arithmetic_error", "Confused pi/3 with pi/4."),
        wrong("sqrt(3)/3", "arithmetic_error", "Returned tangent of pi/6 instead of pi/3."),
    ]),
    entry("ctrig_ts_04", "sin(pi/4)+cos(pi/4)", "medium", "core_trig", [
        wrong("1", "arithmetic_error", "Assumed sine and cosine at pi/4 each equal 1/2."),
        wrong("sqrt(2)/2", "arithmetic_error", "Evaluated only one of the two terms."),
    ]),
    entry("ctrig_ts_05", "sin(pi/3)*cos(pi/6)", "medium", "core_trig", [
        wrong("1/2", "arithmetic_error", "Added the values instead of multiplying."),
        wrong("sqrt(3)/4", "arithmetic_error", "Used the wrong sine value."),
    ]),
    entry("ctrig_ts_06", "tan(pi/4)-sin(pi/6)", "medium", "core_trig", [
        wrong("1/2", "sign_error", "Added sine instead of subtracting it."),
        wrong("3/2", "arithmetic_error", "Used the wrong tangent value."),
    ]),
    entry("ctrig_ts_07", "3*sin(pi/6)+2*cos(pi/3)-tan(pi/4)", "hard", "core_trig", [
        wrong("2", "arithmetic_error", "Dropped the tangent subtraction."),
        wrong("5/2", "arithmetic_error", "Added tangent instead of subtracting it."),
    ]),
    entry("ctrig_ts_08", "sin(pi/2)*cos(pi/4)+tan(pi/6)", "hard", "core_trig", [
        wrong("sqrt(2)/2", "arithmetic_error", "Evaluated only the product term."),
        wrong("sqrt(3)/3", "arithmetic_error", "Evaluated only the tangent term."),
    ]),
    entry("ctrig_ts_09", "2*sin(pi/3)-cos(pi/3)+tan(pi/4)", "hard", "core_trig", [
        wrong("sqrt(3)", "arithmetic_error", "Ignored the cosine subtraction."),
        wrong("1", "arithmetic_error", "Collapsed all terms to one."),
    ]),
    entry("ctrig_ts_10", "4*sin(pi/6)*cos(pi/6)+tan(pi/4)", "hard", "core_trig", [
        wrong("sqrt(3)", "arithmetic_error", "Evaluated the product but omitted tangent."),
        wrong("2", "arithmetic_error", "Used the wrong coefficient on the product."),
    ]),
]

BASIC_TRIG_IDENTITIES_TRAINING = [
    entry("btid_tr_01", "sin^2(x)+cos^2(x)", "easy", "basic_trig_identities", [
        wrong("0", "arithmetic_error", "Incorrectly canceled the identity to zero."),
        wrong("2", "arithmetic_error", "Added the squares instead of applying the identity."),
    ]),
    entry("btid_tr_02", "sin^2(pi/4)+cos^2(pi/4)", "easy", "basic_trig_identities", [
        wrong("sqrt(2)", "arithmetic_error", "Evaluated sine and cosine separately and added."),
        wrong("1/2", "arithmetic_error", "Returned only one squared term."),
    ]),
    entry("btid_tr_03", "cos^2(x)+sin^2(x)", "easy", "basic_trig_identities", [
        wrong("0", "arithmetic_error", "Treated the identity as subtractive."),
        wrong("x", "unknown", "Left the symbolic expression unchanged."),
    ]),
    entry("btid_tr_04", "2*sin^2(x)+2*cos^2(x)", "medium", "basic_trig_identities", [
        wrong("1", "arithmetic_error", "Applied the identity but forgot the outer factor of 2."),
        wrong("4", "arithmetic_error", "Doubled the identity result twice."),
    ]),
    entry("btid_tr_05", "sin^2(x)+cos^2(x)+3", "medium", "basic_trig_identities", [
        wrong("3", "arithmetic_error", "Ignored the identity and kept only the constant."),
        wrong("1", "arithmetic_error", "Applied the identity but dropped the constant."),
    ]),
    entry("btid_tr_06", "5*sin^2(x)+5*cos^2(x)", "medium", "basic_trig_identities", [
        wrong("1", "arithmetic_error", "Applied the identity but omitted the factor of 5."),
        wrong("10", "arithmetic_error", "Multiplied the identity by 5 twice."),
    ]),
    entry("btid_tr_07", "4*(sin^2(x)+cos^2(x))-1", "hard", "basic_trig_identities", [
        wrong("4", "arithmetic_error", "Applied the identity but forgot to subtract 1."),
        wrong("5", "arithmetic_error", "Added 1 instead of subtracting it after substitution."),
    ]),
    entry("btid_tr_08", "sin^2(x)+cos^2(x)+2*sin^2(y)+2*cos^2(y)", "hard", "basic_trig_identities", [
        wrong("2", "arithmetic_error", "Applied the identity for only one angle."),
        wrong("4", "arithmetic_error", "Doubled the full expression instead of factoring."),
    ]),
    entry("btid_tr_09", "sin^2(x)+cos^2(x)+sin^2(x)+cos^2(x)", "hard", "basic_trig_identities", [
        wrong("1", "arithmetic_error", "Applied the identity only once."),
        wrong("4", "arithmetic_error", "Squared the identity result."),
    ]),
    entry("btid_tr_10", "2*sin^2(x)+2*cos^2(x)+sin^2(y)+cos^2(y)", "hard", "basic_trig_identities", [
        wrong("2", "arithmetic_error", "Applied the identity for only one variable."),
        wrong("4", "arithmetic_error", "Treated both pairs as a single identity."),
    ]),
]

BASIC_TRIG_IDENTITIES_TESTING = [
    entry("btid_ts_01", "sin^2(y)+cos^2(y)", "easy", "basic_trig_identities", [
        wrong("0", "arithmetic_error", "Canceled the identity incorrectly."),
        wrong("y", "unknown", "Did not simplify the expression."),
    ]),
    entry("btid_ts_02", "sin^2(pi/6)+cos^2(pi/6)", "easy", "basic_trig_identities", [
        wrong("1/2", "arithmetic_error", "Evaluated one squared term only."),
        wrong("sqrt(3)", "arithmetic_error", "Added sine and cosine before squaring."),
    ]),
    entry("btid_ts_03", "cos^2(t)+sin^2(t)", "easy", "basic_trig_identities", [
        wrong("0", "arithmetic_error", "Subtracted instead of recognizing the identity."),
        wrong("2", "arithmetic_error", "Added the squared terms numerically."),
    ]),
    entry("btid_ts_04", "3*sin^2(x)+3*cos^2(x)", "medium", "basic_trig_identities", [
        wrong("1", "arithmetic_error", "Forgot the coefficient after applying the identity."),
        wrong("6", "arithmetic_error", "Doubled the coefficient incorrectly."),
    ]),
    entry("btid_ts_05", "sin^2(x)+cos^2(x)+5", "medium", "basic_trig_identities", [
        wrong("5", "arithmetic_error", "Ignored the identity completely."),
        wrong("1", "arithmetic_error", "Applied the identity but dropped the constant."),
    ]),
    entry("btid_ts_06", "2*sin^2(x)+4*cos^2(x)+2*sin^2(x)", "medium", "basic_trig_identities", [
        wrong("6", "arithmetic_error", "Added coefficients without factoring the identity."),
        wrong("2", "arithmetic_error", "Combined sine terms but ignored cosine."),
    ]),
    entry("btid_ts_07", "2*(sin^2(x)+cos^2(x))+3*sin^2(y)+3*cos^2(y)", "hard", "basic_trig_identities", [
        wrong("3", "arithmetic_error", "Applied the identity for only one angle."),
        wrong("6", "arithmetic_error", "Added the two identity results instead of 2+3."),
    ]),
    entry("btid_ts_08", "sin^2(pi/4)+cos^2(pi/4)+2*sin^2(pi/3)+2*cos^2(pi/3)", "hard", "basic_trig_identities", [
        wrong("2", "arithmetic_error", "Applied the identity once for both angle pairs."),
        wrong("4", "arithmetic_error", "Evaluated trig values instead of using the identity."),
    ]),
    entry("btid_ts_09", "5*sin^2(x)+5*cos^2(x)-2*sin^2(x)-2*cos^2(x)", "hard", "basic_trig_identities", [
        wrong("7", "arithmetic_error", "Added coefficients instead of subtracting identity pairs."),
        wrong("1", "arithmetic_error", "Subtracted the identity results as 5-2 without grouping."),
    ]),
    entry("btid_ts_10", "sin^2(x)+cos^2(x)+tan^2(x)-tan^2(x)", "hard", "basic_trig_identities", [
        wrong("0", "arithmetic_error", "Canceled all terms to zero."),
        wrong("tan^2(x)", "unknown", "Canceled tangent terms but ignored the identity."),
    ]),
]

TRIG_EQUATIONS_TRAINING = [
    entry("teq_tr_01", "sin(x)=1/2", "easy", "trig_equations", [
        wrong("x=pi/6", "arithmetic_error", "Gave only one angle on the unit circle."),
        wrong("x=pi/3", "arithmetic_error", "Confused sine with cosine values."),
    ]),
    entry("teq_tr_02", "cos(x)=sqrt(3)/2", "easy", "trig_equations", [
        wrong("x=pi/3", "arithmetic_error", "Returned a sine value instead of cosine."),
        wrong("x=pi/6", "arithmetic_error", "Listed only one solution."),
    ]),
    entry("teq_tr_03", "sin(x)=1", "easy", "trig_equations", [
        wrong("x=pi/4", "arithmetic_error", "Confused sine equal to 1 with tangent equal to 1."),
        wrong("x=0", "arithmetic_error", "Returned cosine instead of sine."),
    ]),
    entry("teq_tr_04", "2*sin(x)=1", "medium", "trig_equations", [
        wrong("x=pi/6,x=5pi/6", "arithmetic_error", "Solved before isolating sine."),
        wrong("sin(x)=2", "arithmetic_error", "Divided by 2 on the wrong side."),
    ]),
    entry("teq_tr_05", "cos(x)=-1/2", "medium", "trig_equations", [
        wrong("x=pi/3,x=5pi/3", "sign_error", "Ignored the negative cosine value."),
        wrong("x=2pi/3", "arithmetic_error", "Returned only one quadrant solution."),
    ]),
    entry("teq_tr_06", "tan(x)=1", "medium", "trig_equations", [
        wrong("x=pi/6", "arithmetic_error", "Confused tangent with sine at pi/6."),
        wrong("x=pi/2", "arithmetic_error", "Used an angle where tangent is undefined."),
    ]),
    entry("teq_tr_07", "2*sin(x)-1=0", "hard", "trig_equations", [
        wrong("x=pi/6", "arithmetic_error", "Moved the constant but solved too early."),
        wrong("sin(x)=2", "arithmetic_error", "Added 1 instead of isolating sine."),
    ]),
    entry("teq_tr_08", "sqrt(3)*cos(x)=3/2", "hard", "trig_equations", [
        wrong("x=pi/3,x=5pi/3", "arithmetic_error", "Skipped dividing by sqrt(3)."),
        wrong("cos(x)=3/2", "arithmetic_error", "Divided on the wrong side."),
    ]),
    entry("teq_tr_09", "sin(x)-cos(x)=0", "hard", "trig_equations", [
        wrong("x=pi/6", "arithmetic_error", "Set sine and cosine equal without solving."),
        wrong("x=pi/2", "arithmetic_error", "Used an angle where cosine is zero."),
    ]),
    entry("teq_tr_10", "2*sin(x)+sqrt(3)=0", "hard", "trig_equations", [
        wrong("x=pi/3", "sign_error", "Ignored the negative value after isolating sine."),
        wrong("sin(x)=sqrt(3)/2", "sign_error", "Moved sqrt(3) with the wrong sign."),
    ]),
]

TRIG_EQUATIONS_TESTING = [
    entry("teq_ts_01", "sin(x)=sqrt(3)/2", "easy", "trig_equations", [
        wrong("x=pi/6,x=5pi/6", "arithmetic_error", "Used sine of pi/6 instead of pi/3."),
        wrong("x=pi/4", "arithmetic_error", "Confused with sine equal to sqrt(2)/2."),
    ]),
    entry("teq_ts_02", "cos(x)=1", "easy", "trig_equations", [
        wrong("x=0", "arithmetic_error", "Returned only one full-turn solution."),
        wrong("x=pi/2", "arithmetic_error", "Confused cosine equal to 1 with sine."),
    ]),
    entry("teq_ts_03", "tan(x)=sqrt(3)/3", "easy", "trig_equations", [
        wrong("x=pi/3", "arithmetic_error", "Confused tangent of pi/6 with pi/3."),
        wrong("x=pi/4", "arithmetic_error", "Used tangent equal to 1."),
    ]),
    entry("teq_ts_04", "3*sin(x)=3/2", "medium", "trig_equations", [
        wrong("x=pi/6,x=5pi/6", "arithmetic_error", "Solved before dividing by 3."),
        wrong("sin(x)=3/2", "arithmetic_error", "Multiplied instead of dividing."),
    ]),
    entry("teq_ts_05", "2*cos(x)-1=0", "medium", "trig_equations", [
        wrong("x=pi/3", "arithmetic_error", "Returned only one cosine solution."),
        wrong("cos(x)=2", "arithmetic_error", "Added 1 instead of isolating cosine."),
    ]),
    entry("teq_ts_06", "sqrt(2)*cos(x)=1", "medium", "trig_equations", [
        wrong("x=pi/4", "arithmetic_error", "Listed only one solution."),
        wrong("cos(x)=sqrt(2)", "arithmetic_error", "Divided incorrectly by sqrt(2)."),
    ]),
    entry("teq_ts_07", "sqrt(2)*sin(x)=1", "hard", "trig_equations", [
        wrong("x=pi/4", "arithmetic_error", "Returned only one sine solution."),
        wrong("sin(x)=sqrt(2)", "arithmetic_error", "Skipped isolating sine."),
    ]),
    entry("teq_ts_08", "4*sin(x)=2", "hard", "trig_equations", [
        wrong("x=pi/3,x=2pi/3", "arithmetic_error", "Used the wrong reference angle."),
        wrong("sin(x)=4", "arithmetic_error", "Divided by 4 on the wrong side."),
    ]),
    entry("teq_ts_09", "sin(x)=1/2^1", "hard", "trig_equations", [
        wrong("x=pi/3", "arithmetic_error", "Misread the exponent on the right-hand side."),
        wrong("sin(x)=2", "arithmetic_error", "Treated 2^1 as multiplication by 2."),
    ]),
    entry("teq_ts_10", "2*sin^2(x)=1/2", "hard", "trig_equations", [
        wrong("x=pi/6,x=5pi/6", "arithmetic_error", "Forgot negative reference angles."),
        wrong("sin(x)=1/2", "arithmetic_error", "Stopped after taking the square root."),
    ]),
]

TRIG_TRAINING_DATASET: list[dict] = (
    CORE_TRIG_TRAINING
    + BASIC_TRIG_IDENTITIES_TRAINING
    + TRIG_EQUATIONS_TRAINING
)
TRIG_TESTING_DATASET: list[dict] = (
    CORE_TRIG_TESTING
    + BASIC_TRIG_IDENTITIES_TESTING
    + TRIG_EQUATIONS_TESTING
)

TRIG_TOPICS = (
    "core_trig",
    "basic_trig_identities",
    "trig_equations",
)
