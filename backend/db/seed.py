"""Predefined problem library seeded at application startup."""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import Problem, ProblemWrongAnswer, SolutionPath, SolutionStep
from evaluation_dataset import EVALUATION_DATASET

PREDEFINED_PROBLEMS: list[dict[str, str]] = [
    {
        "id": problem["problem_id"],
        "expression": problem["expression"],
        "expected_final": problem["correct_step"],
        "difficulty": problem["difficulty"],
        "topic": problem["topic"],
    }
    for problem in EVALUATION_DATASET
]


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
    for problem in EVALUATION_DATASET:
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
    for problem in EVALUATION_DATASET:
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
    """Insert single-hop canonical step for each default path; idempotent."""
    for problem in EVALUATION_DATASET:
        problem_id = problem["problem_id"]
        correct_step = problem["correct_step"]
        path = (
            db.query(SolutionPath)
            .filter_by(problem_id=problem_id, is_primary=True)
            .first()
        )
        if path is None:
            continue
        step = (
            db.query(SolutionStep)
            .filter_by(path_id=path.sol_path_id, step_order=1)
            .first()
        )
        if step is None:
            db.add(
                SolutionStep(
                    path_id=path.sol_path_id,
                    step_order=1,
                    sol_step_expression=correct_step,
                )
            )
