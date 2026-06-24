"""Training and testing datasets for function topics (50 problems each).

Each topic includes 10 problems: 3 easy, 3 medium, 4 hard.
"""

from __future__ import annotations

from function_engine import try_build_function_plan


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
    plan = try_build_function_plan(expression)
    return {
        "problem_id": problem_id,
        "expression": expression,
        "correct_step": plan.final_answer,
        "difficulty": difficulty,
        "topic": topic,
        "wrong_answers": wrong_answers,
    }


FUNCTION_EVALUATION_TRAINING = [
    entry("feval_tr_01", "f(x)=x+2|f(1)", "easy", "function_evaluation", [
        wrong("3", "arithmetic_error", "Added 1 to x but used x=1 as the final value only."),
        wrong("x+2", "unknown", "Repeated the rule instead of evaluating at x=1."),
    ]),
    entry("feval_tr_02", "g(x)=4x|g(2)", "easy", "function_evaluation", [
        wrong("6", "arithmetic_error", "Added 4+2 instead of multiplying 4 by 2."),
        wrong("8x", "unknown", "Distributed but left the variable in the answer."),
    ]),
    entry("feval_tr_03", "h(x)=10-x|h(3)", "easy", "function_evaluation", [
        wrong("13", "sign_error", "Added 10+3 instead of subtracting."),
        wrong("7x", "arithmetic_error", "Subtracted incorrectly and kept a variable term."),
    ]),
    entry("feval_tr_04", "f(x)=2x+5|f(3)", "medium", "function_evaluation", [
        wrong("11", "arithmetic_error", "Computed 2(3) correctly but added 5 to get 11 instead of 11 - wait"),
        wrong("6", "arithmetic_error", "Evaluated 2(3) but forgot to add 5."),
    ]),
    entry("feval_tr_05", "f(x)=x^2|f(4)", "medium", "function_evaluation", [
        wrong("8", "arithmetic_error", "Doubled 4 instead of squaring."),
        wrong("16x", "unknown", "Squared symbolically but left the variable attached."),
    ]),
    entry("feval_tr_06", "f(x)=5x-3|f(2)", "medium", "function_evaluation", [
        wrong("7", "arithmetic_error", "Computed 5(2) but subtracted 3 incorrectly."),
        wrong("10", "arithmetic_error", "Added 5+2 instead of multiplying first."),
    ]),
    entry("feval_tr_07", "f(x)=x^2+3x|f(2)", "hard", "function_evaluation", [
        wrong("10", "arithmetic_error", "Found x^2 term but dropped the linear term."),
        wrong("16", "arithmetic_error", "Squared and added coefficients without evaluating each term."),
    ]),
    entry("feval_tr_08", "f(x)=2x+1|f(f(1))", "hard", "function_evaluation", [
        wrong("3", "arithmetic_error", "Evaluated f(1) but stopped before the outer function."),
        wrong("5", "arithmetic_error", "Used f(1)=3 but applied the wrong outer rule."),
    ]),
    entry("feval_tr_09", "p(x)=(x+2)^2|p(1)", "hard", "function_evaluation", [
        wrong("5", "arithmetic_error", "Added inside the parentheses but forgot to square."),
        wrong("3", "distribution_error", "Distributed the square incorrectly."),
    ]),
    entry("feval_tr_10", "r(x)=3x^2-2x+1|r(2)", "hard", "function_evaluation", [
        wrong("9", "arithmetic_error", "Evaluated only the quadratic term."),
        wrong("11", "arithmetic_error", "Dropped the -2x term when substituting."),
    ]),
]

FUNCTION_EVALUATION_TESTING = [
    entry("feval_ts_01", "f(x)=2x+1|f(3)", "easy", "function_evaluation", [
        wrong("6", "arithmetic_error", "Multiplied 2 by 3 but forgot to add 1."),
        wrong("9", "arithmetic_error", "Added 2+3 instead of multiplying first."),
    ]),
    entry("feval_ts_02", "g(x)=x^2|g(2)", "easy", "function_evaluation", [
        wrong("4x", "unknown", "Squared symbolically without evaluating."),
        wrong("6", "arithmetic_error", "Doubled 2 instead of squaring."),
    ]),
    entry("feval_ts_03", "h(x)=5-x|h(1)", "easy", "function_evaluation", [
        wrong("6", "sign_error", "Added instead of subtracting."),
        wrong("4", "arithmetic_error", "Subtracted from the wrong value."),
    ]),
    entry("feval_ts_04", "f(x)=3x-2|f(4)", "medium", "function_evaluation", [
        wrong("10", "arithmetic_error", "Computed 3(4) but subtracted 2 incorrectly."),
        wrong("7", "arithmetic_error", "Added 3+4 instead of multiplying."),
    ]),
    entry("feval_ts_05", "f(x)=x^2+1|f(-2)", "medium", "function_evaluation", [
        wrong("-3", "sign_error", "Squared -2 but kept the negative on the result."),
        wrong("5", "arithmetic_error", "Forgot to add 1 after squaring."),
    ]),
    entry("feval_ts_06", "f(x)=2x^2-x|f(2)", "medium", "function_evaluation", [
        wrong("6", "arithmetic_error", "Evaluated 2(2)^2 but dropped the -x term."),
        wrong("8", "arithmetic_error", "Added terms with the wrong sign on x."),
    ]),
    entry("feval_ts_07", "f(x)=x^2+2x+1|f(-1)", "hard", "function_evaluation", [
        wrong("0x", "arithmetic_error", "Factored correctly in spirit but left a stray variable."),
        wrong("2", "arithmetic_error", "Evaluated only the linear part."),
    ]),
    entry("feval_ts_08", "f(x)=2x+1|f(f(1))", "hard", "function_evaluation", [
        wrong("3", "arithmetic_error", "Stopped after the inner evaluation."),
        wrong("4", "arithmetic_error", "Used the wrong input for the outer function."),
    ]),
    entry("feval_ts_09", "p(x)=x^2-4|p(3)", "hard", "function_evaluation", [
        wrong("5", "arithmetic_error", "Subtracted 4 from 9 incorrectly."),
        wrong("13", "arithmetic_error", "Added 9+4 instead of subtracting."),
    ]),
    entry("feval_ts_10", "r(x)=(x+1)^2|r(2)", "hard", "function_evaluation", [
        wrong("5", "arithmetic_error", "Added inside parentheses but did not square."),
        wrong("3", "distribution_error", "Expanded with the wrong middle term."),
    ]),
]

FUNCTION_COMPOSITION_TRAINING = [
    entry("fcomp_tr_01", "f(x)=x+1,g(x)=2x|f(g(1))", "easy", "function_composition", [
        wrong("2", "arithmetic_error", "Evaluated g(1) but applied the wrong outer rule."),
        wrong("3", "arithmetic_error", "Added g(1) to 1 incorrectly."),
    ]),
    entry("fcomp_tr_02", "f(x)=2x,g(x)=x+3|f(g(0))", "easy", "function_composition", [
        wrong("3", "arithmetic_error", "Stopped after evaluating g(0)."),
        wrong("6", "arithmetic_error", "Doubled g(0) incorrectly."),
    ]),
    entry("fcomp_tr_03", "f(x)=x^2,g(x)=x+1|f(g(0))", "easy", "function_composition", [
        wrong("0", "arithmetic_error", "Squared g(0) incorrectly."),
        wrong("2", "arithmetic_error", "Used g(0)=1 but squared to 2."),
    ]),
    entry("fcomp_tr_04", "f(x)=3x,g(x)=x-1|f(g(3))", "medium", "function_composition", [
        wrong("6", "arithmetic_error", "Evaluated g(3) correctly but multiplied by 3 incorrectly."),
        wrong("8", "arithmetic_error", "Skipped the inner function evaluation."),
    ]),
    entry("fcomp_tr_05", "f(x)=x+2,g(x)=2x|f(g(2))", "medium", "function_composition", [
        wrong("4", "arithmetic_error", "Stopped after g(2)."),
        wrong("8", "arithmetic_error", "Added 2 to g(2) incorrectly."),
    ]),
    entry("fcomp_tr_06", "f(x)=x^2,g(x)=x+1|f(g(1))", "medium", "function_composition", [
        wrong("2", "arithmetic_error", "Squared the wrong value."),
        wrong("3", "arithmetic_error", "Used g(1)=2 instead of g(1)=2 then squared."),
    ]),
    entry("fcomp_tr_07", "f(x)=2x+1,g(x)=x^2|f(g(-2))", "hard", "function_composition", [
        wrong("5", "arithmetic_error", "Evaluated g(-2) but applied the outer rule incorrectly."),
        wrong("9", "arithmetic_error", "Squared -2 incorrectly in the inner step."),
    ]),
    entry("fcomp_tr_08", "f(x)=x+1,g(x)=2x-1,h(x)=x+2|f(g(h(1)))", "hard", "function_composition", [
        wrong("3", "arithmetic_error", "Stopped after the first inner evaluation."),
        wrong("5", "arithmetic_error", "Skipped one layer of composition."),
    ]),
    entry("fcomp_tr_09", "f(x)=x+3,g(x)=2x|f(g(4))", "hard", "function_composition", [
        wrong("8", "arithmetic_error", "Evaluated g(4) but added 3 incorrectly."),
        wrong("11", "arithmetic_error", "Used the wrong order of composition."),
    ]),
    entry("fcomp_tr_10", "f(x)=2x,g(x)=x+1|f(g(g(1)))", "hard", "function_composition", [
        wrong("4", "arithmetic_error", "Stopped after the first composition."),
        wrong("6", "arithmetic_error", "Applied the outer function to the wrong inner value."),
    ]),
]

FUNCTION_COMPOSITION_TESTING = [
    entry("fcomp_ts_01", "f(x)=x+1,g(x)=2x|f(g(2))", "easy", "function_composition", [
        wrong("4", "arithmetic_error", "Stopped after g(2)."),
        wrong("6", "arithmetic_error", "Added instead of applying f to g(2)."),
    ]),
    entry("fcomp_ts_02", "f(x)=2x,g(x)=x+3|f(g(1))", "easy", "function_composition", [
        wrong("4", "arithmetic_error", "Evaluated g(1) but doubled incorrectly."),
        wrong("5", "arithmetic_error", "Added 2+3 instead of composing."),
    ]),
    entry("fcomp_ts_03", "f(x)=x^2,g(x)=x+1|f(g(0))", "easy", "function_composition", [
        wrong("0", "arithmetic_error", "Used g(0)=1 but squared incorrectly."),
        wrong("2", "arithmetic_error", "Forgot to square after g(0)."),
    ]),
    entry("fcomp_ts_04", "f(x)=3x,g(x)=x-1|f(g(3))", "medium", "function_composition", [
        wrong("6", "arithmetic_error", "Multiplied g(3) by 3 incorrectly."),
        wrong("9", "arithmetic_error", "Skipped evaluating g at 3."),
    ]),
    entry("fcomp_ts_05", "f(x)=x+2,g(x)=2x|f(g(2))", "medium", "function_composition", [
        wrong("4", "arithmetic_error", "Stopped after the inner function."),
        wrong("8", "arithmetic_error", "Added 2 to the wrong intermediate value."),
    ]),
    entry("fcomp_ts_06", "f(x)=x^2,g(x)=x+1|f(g(1))", "medium", "function_composition", [
        wrong("3", "arithmetic_error", "Squared g(1) incorrectly."),
        wrong("5", "arithmetic_error", "Used the wrong inner output."),
    ]),
    entry("fcomp_ts_07", "f(x)=2x+1,g(x)=x^2|f(g(-2))", "hard", "function_composition", [
        wrong("5", "arithmetic_error", "Applied the outer linear rule incorrectly."),
        wrong("17", "arithmetic_error", "Squared -2 incorrectly."),
    ]),
    entry("fcomp_ts_08", "f(x)=x+1,g(x)=2x-1,h(x)=x+2|f(g(h(1)))", "hard", "function_composition", [
        wrong("3", "arithmetic_error", "Stopped after one layer of composition."),
        wrong("4", "arithmetic_error", "Evaluated layers in the wrong order."),
    ]),
    entry("fcomp_ts_09", "f(x)=x+3,g(x)=2x|f(g(3))", "hard", "function_composition", [
        wrong("9", "arithmetic_error", "Added 3 to g(3) incorrectly."),
        wrong("12", "arithmetic_error", "Used g(3)=6 but finished with the wrong outer value."),
    ]),
    entry("fcomp_ts_10", "f(x)=2x,g(x)=x+1|f(g(g(2)))", "hard", "function_composition", [
        wrong("6", "arithmetic_error", "Stopped after the first nested composition."),
        wrong("8", "arithmetic_error", "Applied the outer function too early."),
    ]),
]

INVERSE_FUNCTIONS_TRAINING = [
    entry("finv_tr_01", "f(x)=2x|finv(x)", "easy", "inverse_functions", [
        wrong("2x", "unknown", "Repeated the original function."),
        wrong("x-2", "sign_error", "Subtracted instead of dividing."),
    ]),
    entry("finv_tr_02", "f(x)=x+3|finv(x)", "easy", "inverse_functions", [
        wrong("x+3", "unknown", "Did not invert the operation."),
        wrong("x/3", "arithmetic_error", "Divided instead of subtracting."),
    ]),
    entry("finv_tr_03", "f(x)=x-5|finv(x)", "easy", "inverse_functions", [
        wrong("x-5", "unknown", "Repeated the original rule."),
        wrong("x+5", "sign_error", "Added 5 but kept the wrong structure."),
    ]),
    entry("finv_tr_04", "f(x)=3x+1|finv(x)", "medium", "inverse_functions", [
        wrong("(x+1)/3", "sign_error", "Moved the constant with the wrong sign."),
        wrong("3x-1", "unknown", "Reversed operations in the wrong order."),
    ]),
    entry("finv_tr_05", "f(x)=(x-2)/4|finv(x)", "medium", "inverse_functions", [
        wrong("4x-2", "arithmetic_error", "Multiplied and added with the wrong signs."),
        wrong("(x+2)/4", "sign_error", "Flipped the sign on the constant term."),
    ]),
    entry("finv_tr_06", "f(x)=2x+5|finv(x)", "medium", "inverse_functions", [
        wrong("(x+5)/2", "sign_error", "Moved +5 with the wrong sign."),
        wrong("2x-5", "unknown", "Subtracted instead of solving for the inverse."),
    ]),
    entry("finv_tr_07", "f(x)=(2x+1)/3|finv(x)", "hard", "inverse_functions", [
        wrong("(3x+1)/2", "arithmetic_error", "Swapped coefficients incorrectly."),
        wrong("3x-1", "unknown", "Did not solve for x in terms of y."),
    ]),
    entry("finv_tr_08", "f(x)=5-2x|finv(x)", "hard", "inverse_functions", [
        wrong("(x-5)/2", "sign_error", "Moved 5 with the wrong sign."),
        wrong("(5-x)/2", "arithmetic_error", "Inverted the slope incorrectly."),
    ]),
    entry("finv_tr_09", "f(x)=4x-8|finv(x)", "hard", "inverse_functions", [
        wrong("(x-8)/4", "sign_error", "Moved -8 with the wrong sign."),
        wrong("4x+8", "unknown", "Added instead of solving for the inverse."),
    ]),
    entry("finv_tr_10", "f(x)=(x+3)/2|finv(x)", "hard", "inverse_functions", [
        wrong("2x+3", "unknown", "Found the forward rule instead of the inverse."),
        wrong("2x-3", "sign_error", "Multiplied and moved the constant with the wrong sign."),
    ]),
]

INVERSE_FUNCTIONS_TESTING = [
    entry("finv_ts_01", "f(x)=2x|finv(x)", "easy", "inverse_functions", [
        wrong("2x", "unknown", "Returned the original function."),
        wrong("x/2", "arithmetic_error", "Divided the wrong expression."),
    ]),
    entry("finv_ts_02", "f(x)=x+3|finv(x)", "easy", "inverse_functions", [
        wrong("x+3", "unknown", "Did not invert addition."),
        wrong("x-3", "sign_error", "Subtracted from the wrong side."),
    ]),
    entry("finv_ts_03", "f(x)=x-5|finv(x)", "easy", "inverse_functions", [
        wrong("x-5", "unknown", "Repeated the original rule."),
        wrong("x+5", "sign_error", "Added 5 but did not solve for the input."),
    ]),
    entry("finv_ts_04", "f(x)=3x+1|finv(x)", "medium", "inverse_functions", [
        wrong("(x+1)/3", "sign_error", "Moved +1 with the wrong sign."),
        wrong("3x-1", "unknown", "Reversed operations incorrectly."),
    ]),
    entry("finv_ts_05", "f(x)=(x-2)/4|finv(x)", "medium", "inverse_functions", [
        wrong("4x-2", "arithmetic_error", "Inverted multiply/divide in the wrong order."),
        wrong("(x+2)/4", "sign_error", "Used the wrong sign on the constant."),
    ]),
    entry("finv_ts_06", "f(x)=2x+5|finv(x)", "medium", "inverse_functions", [
        wrong("(x+5)/2", "sign_error", "Moved +5 with the wrong sign."),
        wrong("2x-5", "unknown", "Subtracted instead of inverting."),
    ]),
    entry("finv_ts_07", "f(x)=(2x+1)/3|finv(x)", "hard", "inverse_functions", [
        wrong("(3x+1)/2", "arithmetic_error", "Swapped coefficients incorrectly."),
        wrong("3x-1", "unknown", "Did not isolate x correctly."),
    ]),
    entry("finv_ts_08", "f(x)=5-2x|finv(x)", "hard", "inverse_functions", [
        wrong("(x-5)/2", "sign_error", "Moved 5 with the wrong sign."),
        wrong("(5+x)/2", "arithmetic_error", "Inverted the slope incorrectly."),
    ]),
    entry("finv_ts_09", "f(x)=4x-8|finv(x)", "hard", "inverse_functions", [
        wrong("(x-8)/4", "sign_error", "Moved -8 with the wrong sign."),
        wrong("4x+8", "unknown", "Used the forward rule."),
    ]),
    entry("finv_ts_10", "f(x)=(x+3)/2|finv(x)", "hard", "inverse_functions", [
        wrong("2x+3", "unknown", "Found the forward function."),
        wrong("2x-3", "sign_error", "Moved +3 with the wrong sign."),
    ]),
]

EXPONENTIAL_FUNCTIONS_TRAINING = [
    entry("fexp_tr_01", "2^3*2^2", "easy", "exponential_functions", [
        wrong("64", "arithmetic_error", "Multiplied bases instead of adding exponents."),
        wrong("2^6", "arithmetic_error", "Added exponents on different bases."),
    ]),
    entry("fexp_tr_02", "3^2*3^1", "easy", "exponential_functions", [
        wrong("9", "arithmetic_error", "Stopped after evaluating one factor."),
        wrong("3^3", "arithmetic_error", "Added exponents but did not finish."),
    ]),
    entry("fexp_tr_03", "5^2/5", "easy", "exponential_functions", [
        wrong("5", "arithmetic_error", "Subtracted exponents incorrectly."),
        wrong("25", "arithmetic_error", "Evaluated the numerator only."),
    ]),
    entry("fexp_tr_04", "(2^2)^3", "medium", "exponential_functions", [
        wrong("64", "arithmetic_error", "Multiplied base by exponent incorrectly."),
        wrong("2^5", "arithmetic_error", "Added exponents instead of multiplying them."),
    ]),
    entry("fexp_tr_05", "2^3*2^4", "medium", "exponential_functions", [
        wrong("2^12", "arithmetic_error", "Multiplied exponents instead of adding."),
        wrong("128", "arithmetic_error", "Evaluated each power separately and multiplied."),
    ]),
    entry("fexp_tr_06", "(3^2)^2", "medium", "exponential_functions", [
        wrong("3^4", "arithmetic_error", "Added exponents instead of multiplying."),
        wrong("81", "arithmetic_error", "Skipped the power-of-a-power step."),
    ]),
    entry("fexp_tr_07", "2^3*2^4*2", "hard", "exponential_functions", [
        wrong("2^7", "arithmetic_error", "Forgot one factor when combining exponents."),
        wrong("256", "arithmetic_error", "Evaluated each term separately."),
    ]),
    entry("fexp_tr_08", "(2^2)^2*2^3", "hard", "exponential_functions", [
        wrong("2^7", "arithmetic_error", "Combined exponents in the wrong order."),
        wrong("128", "arithmetic_error", "Skipped the nested power step."),
    ]),
    entry("fexp_tr_09", "3^2*3^2", "hard", "exponential_functions", [
        wrong("3^4", "arithmetic_error", "Added exponents but did not evaluate."),
        wrong("18", "arithmetic_error", "Multiplied bases instead of adding exponents."),
    ]),
    entry("fexp_tr_10", "(2^3)^2", "hard", "exponential_functions", [
        wrong("2^5", "arithmetic_error", "Added exponents instead of multiplying."),
        wrong("64", "arithmetic_error", "Evaluated inside parentheses only."),
    ]),
]

EXPONENTIAL_FUNCTIONS_TESTING = [
    entry("fexp_ts_01", "2^3*2^2", "easy", "exponential_functions", [
        wrong("64", "arithmetic_error", "Multiplied bases instead of adding exponents."),
        wrong("2^6", "arithmetic_error", "Added exponents incorrectly."),
    ]),
    entry("fexp_ts_02", "3^2*3", "easy", "exponential_functions", [
        wrong("9", "arithmetic_error", "Evaluated only one factor."),
        wrong("3^3", "arithmetic_error", "Combined exponents but did not finish."),
    ]),
    entry("fexp_ts_03", "5^3/5^2", "easy", "exponential_functions", [
        wrong("5", "arithmetic_error", "Subtracted exponents incorrectly."),
        wrong("125", "arithmetic_error", "Evaluated the numerator only."),
    ]),
    entry("fexp_ts_04", "(2^2)^3", "medium", "exponential_functions", [
        wrong("2^5", "arithmetic_error", "Added exponents instead of multiplying."),
        wrong("64", "arithmetic_error", "Skipped the power-of-a-power step."),
    ]),
    entry("fexp_ts_05", "2^2*2^5", "medium", "exponential_functions", [
        wrong("2^10", "arithmetic_error", "Multiplied exponents instead of adding."),
        wrong("128", "arithmetic_error", "Evaluated each term separately."),
    ]),
    entry("fexp_ts_06", "(3^2)^2", "medium", "exponential_functions", [
        wrong("3^4", "arithmetic_error", "Added instead of multiplying exponents."),
        wrong("81", "arithmetic_error", "Skipped the intermediate power step."),
    ]),
    entry("fexp_ts_07", "2^2*2^3*2", "hard", "exponential_functions", [
        wrong("2^5", "arithmetic_error", "Forgot one exponent when combining."),
        wrong("128", "arithmetic_error", "Evaluated each factor separately."),
    ]),
    entry("fexp_ts_08", "(2^2)^2*2^2", "hard", "exponential_functions", [
        wrong("2^6", "arithmetic_error", "Combined exponents in the wrong order."),
        wrong("64", "arithmetic_error", "Skipped the nested power step."),
    ]),
    entry("fexp_ts_09", "3^2*3^3", "hard", "exponential_functions", [
        wrong("3^6", "arithmetic_error", "Multiplied exponents instead of adding."),
        wrong("243", "arithmetic_error", "Evaluated each power separately."),
    ]),
    entry("fexp_ts_10", "(2^3)^2", "hard", "exponential_functions", [
        wrong("2^5", "arithmetic_error", "Added exponents instead of multiplying."),
        wrong("64", "arithmetic_error", "Evaluated inside parentheses only."),
    ]),
]

LOGARITHMS_TRAINING = [
    entry("flog_tr_01", "log(8,2)", "easy", "logarithms", [
        wrong("4", "arithmetic_error", "Divided 8 by 2 once instead of finding the power."),
        wrong("2", "arithmetic_error", "Confused the base with the answer."),
    ]),
    entry("flog_tr_02", "log(9,3)", "easy", "logarithms", [
        wrong("3", "arithmetic_error", "Divided instead of finding the exponent."),
        wrong("6", "arithmetic_error", "Subtracted base from argument."),
    ]),
    entry("flog_tr_03", "log(16,2)", "easy", "logarithms", [
        wrong("8", "arithmetic_error", "Halved the argument once."),
        wrong("4", "arithmetic_error", "Counted divisions instead of powers."),
    ]),
    entry("flog_tr_04", "log(4,2)+log(2,2)", "medium", "logarithms", [
        wrong("3", "arithmetic_error", "Added the logs without combining arguments."),
        wrong("log(6,2)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
    entry("flog_tr_05", "log(27,3)-log(3,3)", "medium", "logarithms", [
        wrong("2", "arithmetic_error", "Subtracted log values without combining first."),
        wrong("log(24,3)", "arithmetic_error", "Subtracted arguments instead of dividing."),
    ]),
    entry("flog_tr_06", "log(32,2)-log(4,2)", "medium", "logarithms", [
        wrong("4", "arithmetic_error", "Subtracted results without combining logs."),
        wrong("log(28,2)", "arithmetic_error", "Subtracted arguments instead of dividing."),
    ]),
    entry("flog_tr_07", "log(64,2)+log(8,2)", "hard", "logarithms", [
        wrong("9", "arithmetic_error", "Added log values without combining arguments."),
        wrong("log(72,2)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
    entry("flog_tr_08", "log(81,3)/log(9,3)", "hard", "logarithms", [
        wrong("3", "arithmetic_error", "Divided arguments instead of using log rules."),
        wrong("1", "arithmetic_error", "Canceled logs incorrectly."),
    ]),
    entry("flog_tr_09", "log(100,10)+log(10,10)", "hard", "logarithms", [
        wrong("3", "arithmetic_error", "Added logs without combining arguments."),
        wrong("log(110,10)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
    entry("flog_tr_10", "log(16,2)+log(4,2)", "hard", "logarithms", [
        wrong("6", "arithmetic_error", "Added log values directly."),
        wrong("log(20,2)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
]

LOGARITHMS_TESTING = [
    entry("flog_ts_01", "log(8,2)", "easy", "logarithms", [
        wrong("4", "arithmetic_error", "Divided once instead of finding the exponent."),
        wrong("2", "arithmetic_error", "Confused the base with the answer."),
    ]),
    entry("flog_ts_02", "log(9,3)", "easy", "logarithms", [
        wrong("3", "arithmetic_error", "Divided instead of exponentiating."),
        wrong("6", "arithmetic_error", "Subtracted base from argument."),
    ]),
    entry("flog_ts_03", "log(16,2)", "easy", "logarithms", [
        wrong("8", "arithmetic_error", "Halved once."),
        wrong("4", "arithmetic_error", "Counted divisions instead of powers."),
    ]),
    entry("flog_ts_04", "log(4,2)+log(2,2)", "medium", "logarithms", [
        wrong("3", "arithmetic_error", "Added logs without combining arguments."),
        wrong("log(6,2)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
    entry("flog_ts_05", "log(27,3)-log(3,3)", "medium", "logarithms", [
        wrong("2", "arithmetic_error", "Subtracted log values without combining."),
        wrong("log(24,3)", "arithmetic_error", "Subtracted arguments instead of dividing."),
    ]),
    entry("flog_ts_06", "log(32,2)-log(4,2)", "medium", "logarithms", [
        wrong("4", "arithmetic_error", "Subtracted results without combining logs."),
        wrong("log(28,2)", "arithmetic_error", "Subtracted arguments instead of dividing."),
    ]),
    entry("flog_ts_07", "log(64,2)+log(8,2)", "hard", "logarithms", [
        wrong("9", "arithmetic_error", "Added log values directly."),
        wrong("log(72,2)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
    entry("flog_ts_08", "log(81,3)/log(9,3)", "hard", "logarithms", [
        wrong("3", "arithmetic_error", "Divided arguments instead of using log rules."),
        wrong("1", "arithmetic_error", "Canceled logs incorrectly."),
    ]),
    entry("flog_ts_09", "log(100,10)+log(10,10)", "hard", "logarithms", [
        wrong("3", "arithmetic_error", "Added logs without combining arguments."),
        wrong("log(110,10)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
    entry("flog_ts_10", "log(16,2)+log(4,2)", "hard", "logarithms", [
        wrong("6", "arithmetic_error", "Added log values directly."),
        wrong("log(20,2)", "arithmetic_error", "Added arguments instead of multiplying."),
    ]),
]

FUNCTION_TRAINING_DATASET: list[dict] = (
    FUNCTION_EVALUATION_TRAINING
    + FUNCTION_COMPOSITION_TRAINING
    + INVERSE_FUNCTIONS_TRAINING
    + EXPONENTIAL_FUNCTIONS_TRAINING
    + LOGARITHMS_TRAINING
)

FUNCTION_TESTING_DATASET: list[dict] = (
    FUNCTION_EVALUATION_TESTING
    + FUNCTION_COMPOSITION_TESTING
    + INVERSE_FUNCTIONS_TESTING
    + EXPONENTIAL_FUNCTIONS_TESTING
    + LOGARITHMS_TESTING
)

FUNCTION_TOPICS = (
    "function_evaluation",
    "function_composition",
    "inverse_functions",
    "exponential_functions",
    "logarithms",
)
