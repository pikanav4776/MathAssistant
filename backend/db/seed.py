"""Predefined problem library seeded at application startup."""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import Problem, ProblemWrongAnswer
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
