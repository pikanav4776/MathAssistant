import pytest

from step_engine import UnsupportedProblemError, build_solution_plan, detect_topic


@pytest.mark.parametrize(
    "expression,topic",
    [
        ("2(x+3)", "distribution"),
        ("(x+2)(x+3)", "foil"),
        ("5x+3-2x", "linear_steps"),
        ("x^2 + x + 1", "linear_steps"),
    ],
)
def test_detect_topic_supported(expression, topic):
    assert detect_topic(expression) == topic


def test_build_solution_plan_single_hop():
    plan = build_solution_plan("2(x+3)")
    assert plan.subject == "algebra"
    assert plan.topic == "distribution"
    assert len(plan.steps) == 1
    assert "2" in plan.steps[0]
    assert "x" in plan.steps[0]
    assert "6" in plan.steps[0]


@pytest.mark.parametrize(
    "expression",
    [
        "2x+3=7",
        "x>2",
        "sqrt(x)",
        "sin(x)",
        "2@@3",
    ],
)
def test_build_solution_plan_rejects_unsupported(expression):
    with pytest.raises(UnsupportedProblemError):
        build_solution_plan(expression)
