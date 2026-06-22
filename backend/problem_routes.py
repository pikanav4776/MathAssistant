"""Starter problem list endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Problem
from db.starter_problems import STARTER_PROBLEM_IDS, filter_starter_problem_ids

router = APIRouter(tags=["problems"])


class StarterProblemItem(BaseModel):
    id: str
    expression: str
    difficulty: str | None
    topic: str | None


@router.get("/problems/starter", response_model=list[StarterProblemItem])
def list_starter_problems(
    difficulty: str | None = None,
    topic: str | None = None,
    db: Session = Depends(get_db),
):
    ids = filter_starter_problem_ids(difficulty=difficulty, topic=topic)
    if not ids:
        raise HTTPException(
            status_code=404,
            detail={"error": "no_starter_problems", "message": "No starter problems match the filters."},
        )

    rows = db.query(Problem).filter(Problem.id.in_(ids)).all()
    by_id = {row.id: row for row in rows}

    items: list[StarterProblemItem] = []
    for problem_id in ids:
        row = by_id.get(problem_id)
        if row is None:
            continue
        items.append(
            StarterProblemItem(
                id=row.id,
                expression=row.expression,
                difficulty=row.difficulty,
                topic=row.topic,
            )
        )

    if not items:
        raise HTTPException(
            status_code=404,
            detail={"error": "no_starter_problems", "message": "Starter problems are not seeded yet."},
        )
    return items
