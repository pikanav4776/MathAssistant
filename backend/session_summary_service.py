"""Persist session_summaries rows when a tutoring session ends."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.models import Attempt, SessionSummary as SessionSummaryRecord, TutoringSession


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def final_error_type_for_session(db: Session, session_id: str) -> str | None:
    row = (
        db.query(Attempt)
        .filter_by(session_id=session_id, is_equivalent=False)
        .order_by(Attempt.timestamp.desc())
        .first()
    )
    return row.error_type if row else None


def upsert_session_summary(
    db: Session,
    session_row: TutoringSession,
    *,
    completed: bool,
    revealed_solution: bool,
) -> None:
    now = _utc_now()
    duration_seconds: int | None = None
    if session_row.created_at is not None:
        created = session_row.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        duration_seconds = max(0, int((now - created).total_seconds()))

    existing = (
        db.query(SessionSummaryRecord)
        .filter_by(session_id=session_row.session_id)
        .first()
    )
    payload = {
        "user_id": session_row.user_id,
        "problem_id": session_row.problem_id,
        "total_attempts": session_row.attempt_count,
        "incorrect_attempts": session_row.incorrect_attempt_count,
        "completed": completed,
        "revealed_solution": revealed_solution,
        "duration_seconds": duration_seconds,
        "final_error_type": final_error_type_for_session(db, session_row.session_id),
        "completed_at": now,
    }
    if existing is None:
        db.add(SessionSummaryRecord(session_id=session_row.session_id, **payload))
    else:
        for key, value in payload.items():
            setattr(existing, key, value)