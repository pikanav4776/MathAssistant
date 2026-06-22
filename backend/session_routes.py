"""Session finalize and user history endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.deps import get_current_user, get_optional_user
from db.database import get_db
from db.models import Problem, SessionSummary as SessionSummaryRecord, TutoringSession, User
from session_access import assert_session_access
from session_summary_service import upsert_session_summary

router = APIRouter(tags=["sessions"])


class FinalizeSessionRequest(BaseModel):
    completed: bool = False
    revealed_solution: bool = False


class FinalizeSessionResponse(BaseModel):
    session_id: str
    summarized: bool


class UserSessionHistoryItem(BaseModel):
    session_id: str
    problem_id: str
    problem_expression: str
    completed: bool
    revealed_solution: bool
    total_attempts: int
    incorrect_attempts: int
    duration_seconds: int | None
    completed_at: datetime | None


@router.post("/session/{session_id}/finalize", response_model=FinalizeSessionResponse)
def finalize_session(
    session_id: str,
    data: FinalizeSessionRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    session_row = db.query(TutoringSession).filter_by(session_id=session_id).first()
    if session_row is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found"})

    assert_session_access(session_row, current_user)

    session_row.completed = data.completed or data.revealed_solution
    upsert_session_summary(
        db,
        session_row,
        completed=data.completed,
        revealed_solution=data.revealed_solution,
    )
    db.commit()
    return FinalizeSessionResponse(session_id=session_id, summarized=True)


@router.get("/auth/me/sessions", response_model=list[UserSessionHistoryItem])
def list_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(SessionSummaryRecord, Problem)
        .join(Problem, Problem.id == SessionSummaryRecord.problem_id)
        .filter(SessionSummaryRecord.user_id == current_user.id)
        .order_by(SessionSummaryRecord.completed_at.desc().nullslast())
        .limit(25)
        .all()
    )
    return [
        UserSessionHistoryItem(
            session_id=summary.session_id,
            problem_id=summary.problem_id,
            problem_expression=problem.expression,
            completed=summary.completed,
            revealed_solution=summary.revealed_solution,
            total_attempts=summary.total_attempts,
            incorrect_attempts=summary.incorrect_attempts,
            duration_seconds=summary.duration_seconds,
            completed_at=summary.completed_at,
        )
        for summary, problem in rows
    ]