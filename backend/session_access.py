"""Session ownership checks for guest and authenticated users."""

from __future__ import annotations

from fastapi import HTTPException

from db.models import TutoringSession, User, UserRole


def assert_session_access(session_row: TutoringSession, user: User | None) -> None:
    owner_id = session_row.user_id
    if owner_id is None:
        return
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Sign in to access this session."},
        )
    if user.id != owner_id and user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "You do not have access to this session."},
        )