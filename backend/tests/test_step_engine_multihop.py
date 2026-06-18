from step_engine import build_solution_plan


def test_multihop_distribution_plus_constant():
    plan = build_solution_plan("2(x+3)+4")
    assert len(plan.steps) >= 2
    assert "4" in plan.steps[0]
    assert plan.final_answer == plan.steps[-1]


def test_multihop_foil_plus_constant():
    plan = build_solution_plan("(x+1)(x+2)+3")
    assert len(plan.steps) >= 2
    assert "x" in plan.steps[0]
    assert plan.final_answer == plan.steps[-1]
