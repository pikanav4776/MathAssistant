"""Test helpers for seeding problems and tutoring sessions."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from db.models import Problem, SolutionPath, SolutionStep, TutoringSession
from step_engine import build_solution_plan


def seed_problem_with_plan(
    db: Session,
    expression: str,
    *,
    problem_id: str | None = None,
) -> tuple[Problem, list[SolutionStep]]:
    plan = build_solution_plan(expression)
    pid = problem_id or f"test_{uuid.uuid4().hex[:12]}"
    problem = Problem(
        id=pid,
        expression=expression,
        expected_final=plan.final_answer,
        topic=plan.topic,
    )
    db.add(problem)
    db.flush()

    path = SolutionPath(problem_id=pid, sol_path_name="default", is_primary=True)
    db.add(path)
    db.flush()

    step_rows: list[SolutionStep] = []
    for index, step_expr in enumerate(plan.steps, start=1):
        row = SolutionStep(
            path_id=path.sol_path_id,
            step_order=index,
            sol_step_expression=step_expr,
        )
        db.add(row)
        step_rows.append(row)
    db.flush()
    return problem, step_rows


def start_tutoring_session(
    db: Session,
    problem: Problem,
    steps: list[SolutionStep],
) -> TutoringSession:
    session = TutoringSession(
        session_id=str(uuid.uuid4()),
        problem_id=problem.id,
        attempt_count=0,
        incorrect_attempt_count=0,
        hint_level=1,
        current_step_id=None,
        current_expression=problem.expression,
        completed=False,
    )
    db.add(session)
    db.flush()
    return session
