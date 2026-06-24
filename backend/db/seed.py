"""Predefined problem library seeded at application startup."""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import Problem, ProblemWrongAnswer, SolutionPath, SolutionStep
from function_datasets import FUNCTION_TESTING_DATASET, FUNCTION_TRAINING_DATASET
from trig_datasets import TRIG_TESTING_DATASET, TRIG_TRAINING_DATASET
from evaluation_dataset import EVALUATION_DATASET
from step_engine import build_solution_plan

PREDEFINED_PROBLEMS: list[dict[str, str]] = [
    {
        "id": problem["problem_id"],
        "expression": problem["expression"],
        "expected_final": problem["correct_step"],
        "difficulty": problem["difficulty"],
        "topic": problem["topic"],
    }
    for problem in (
        EVALUATION_DATASET
        + FUNCTION_TRAINING_DATASET
        + FUNCTION_TESTING_DATASET
        + TRIG_TRAINING_DATASET
        + TRIG_TESTING_DATASET
    )
]

ALL_SEEDED_PROBLEMS = (
    EVALUATION_DATASET
    + FUNCTION_TRAINING_DATASET
    + FUNCTION_TESTING_DATASET
    + TRIG_TRAINING_DATASET
    + TRIG_TESTING_DATASET
)


def seed_problems(db: Session) -> None:
    """Insert predefined problems; safe to call on every startup (idempotent)."""
    for problem in PREDEFINED_PROBLEMS:
        stmt = (
            insert(Problem)
            .values(**problem)
            .on_conflict_do_nothing(index_elements=["id"])
        )
        db.execute(stmt)


def seed_wrong_answers(db: Session) -> None:
    """Insert canonical wrong answers; safe to call on every startup (idempotent)."""
    for problem in ALL_SEEDED_PROBLEMS:
        for wrong in problem["wrong_answers"]:
            stmt = (
                insert(ProblemWrongAnswer)
                .values(
                    problem_id=problem["problem_id"],
                    wrong_step=wrong["wrong_step"],
                    error_type=wrong["expected_error_type"],
                    description=wrong["description"],
                )
                .on_conflict_do_nothing(constraint="uq_problem_wrong_step")
            )
            db.execute(stmt)


def seed_solution_paths(db: Session) -> None:
    """Insert default solution path per problem; idempotent."""
    for problem in ALL_SEEDED_PROBLEMS:
        problem_id = problem["problem_id"]
        existing = (
            db.query(SolutionPath)
            .filter_by(problem_id=problem_id, is_primary=True)
            .first()
        )
        if existing is None:
            db.add(
                SolutionPath(
                    problem_id=problem_id,
                    sol_path_name="default",
                    is_primary=True,
                )
            )
    db.flush()


def seed_solution_steps(db: Session) -> None:
    """Insert canonical solution steps from step_engine for each default path; idempotent."""
    for problem in ALL_SEEDED_PROBLEMS:
        problem_id = problem["problem_id"]
        path = (
            db.query(SolutionPath)
            .filter_by(problem_id=problem_id, is_primary=True)
            .first()
        )
        if path is None:
            continue

        has_steps = (
            db.query(SolutionStep)
            .filter_by(path_id=path.sol_path_id)
            .first()
            is not None
        )
        if has_steps:
            continue

        plan = build_solution_plan(problem["expression"])
        for order, step_expr in enumerate(plan.steps, start=1):
            step = (
                db.query(SolutionStep)
                .filter_by(path_id=path.sol_path_id, step_order=order)
                .first()
            )
            if step is None:
                db.add(
                    SolutionStep(
                        path_id=path.sol_path_id,
                        step_order=order,
                        sol_step_expression=step_expr,
                    )
                )
