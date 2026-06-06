"""Predefined problem library seeded at application startup."""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import Problem

PREDEFINED_PROBLEMS: list[dict[str, str]] = [
    {
        "id": "dist_001",
        "expression": "2(x+3)",
        "expected_final": "2x+6",
        "difficulty": "easy",
        "topic": "distribution",
    },
    {
        "id": "dist_002",
        "expression": "3(x-4)",
        "expected_final": "3x-12",
        "difficulty": "easy",
        "topic": "distribution",
    },
    {
        "id": "dist_003",
        "expression": "4(2x+5)",
        "expected_final": "8x+20",
        "difficulty": "medium",
        "topic": "distribution",
    },
    {
        "id": "dist_004",
        "expression": "2(3x^2+x+1)",
        "expected_final": "6x^2+2x+2",
        "difficulty": "medium",
        "topic": "distribution",
    },
    {
        "id": "sign_001",
        "expression": "x+3-2x+1",
        "expected_final": "-x+4",
        "difficulty": "easy",
        "topic": "simplification",
    },
    {
        "id": "sign_002",
        "expression": "5x-3-7x+2",
        "expected_final": "-2x-1",
        "difficulty": "easy",
        "topic": "simplification",
    },
    {
        "id": "sign_003",
        "expression": "-(x+4)+2x",
        "expected_final": "x-4",
        "difficulty": "medium",
        "topic": "simplification",
    },
    {
        "id": "arith_001",
        "expression": "3x+2x",
        "expected_final": "5x",
        "difficulty": "easy",
        "topic": "simplification",
    },
    {
        "id": "arith_002",
        "expression": "4x^2+3x^2-x",
        "expected_final": "7x^2-x",
        "difficulty": "medium",
        "topic": "simplification",
    },
    {
        "id": "arith_003",
        "expression": "2x+3+4x-1",
        "expected_final": "6x+2",
        "difficulty": "easy",
        "topic": "simplification",
    },
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
