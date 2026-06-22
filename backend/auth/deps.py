"""FastAPI dependencies for optional and required authentication."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.jwt_utils import decode_token
from db.database import get_db
from db.models import User, UserRole

_bearer = HTTPBearer(auto_error=False)


def _user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
    return db.query(User).filter_by(id=user_id).first()


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    return _user_from_token(credentials.credentials, db)


def get_current_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "not_authenticated",
                "message": "Authentication required.",
            },
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "message": "Admin role required.",
            },
        )
    return user