"""Register, login, and profile endpoints."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.auth_utils import hash_password, verify_password
from auth.deps import get_current_user
from auth.jwt_utils import create_token
from db.database import get_db
from db.models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserProfile(BaseModel):
    id: int
    email: str
    display_name: str | None
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_email(email: str) -> None:
    if not _EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_email", "message": "Invalid email address."},
        )


def _user_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = _normalize_email(data.email)
    _validate_email(email)

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        display_name=(data.display_name or "").strip() or None,
        role=UserRole.USER.value,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"error": "email_taken", "message": "An account with this email already exists."},
        ) from exc

    db.refresh(user)
    token = create_token(user.id, user.role)
    return AuthResponse(access_token=token, user=_user_profile(user))


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = _normalize_email(data.email)
    user = db.query(User).filter_by(email=email).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_credentials", "message": "Invalid email or password."},
        )

    user.last_login_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.role)
    return AuthResponse(access_token=token, user=_user_profile(user))


@router.get("/me", response_model=UserProfile)
def me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return _user_profile(current_user)