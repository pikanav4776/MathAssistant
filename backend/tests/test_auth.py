"""Tests for Phase 1 auth scaffolding and User model constraints."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import jwt
from auth.auth_utils import hash_password, verify_password
from auth.jwt_utils import create_token, decode_token
from db.models import User, UserRole


def test_hash_and_verify_password_round_trip() -> None:
    hashed = hash_password("s3cret-p@ss")
    assert hashed != "s3cret-p@ss"
    assert verify_password("s3cret-p@ss", hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_token() -> None:
    token = create_token(user_id=42, role=UserRole.USER.value)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "user"
    assert "exp" in payload


def test_decode_token_rejects_tampered_signature() -> None:
    token = create_token(user_id=1, role=UserRole.ADMIN.value)
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1] + ".invalid"
    with pytest.raises(jwt.PyJWTError):
        decode_token(tampered)


def test_user_model_persists_with_default_role(db_session: Session) -> None:
    user = User(
        email="alice@example.com",
        password_hash=hash_password("alice-pass"),
        display_name="Alice",
    )
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert user.role == UserRole.USER.value
    assert user.created_at is not None
    assert user.last_login_at is None


def test_user_email_must_be_unique(db_session: Session) -> None:
    db_session.add(
        User(
            email="dup@example.com",
            password_hash=hash_password("one"),
        )
    )
    db_session.flush()
    db_session.add(
        User(
            email="dup@example.com",
            password_hash=hash_password("two"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_role_check_constraint(db_session: Session) -> None:
    db_session.add(
        User(
            email="bad-role@example.com",
            password_hash=hash_password("pw"),
            role="student",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_accepts_admin_role(db_session: Session) -> None:
    user = User(
        email="admin@example.com",
        password_hash=hash_password("admin-pass"),
        role=UserRole.ADMIN.value,
    )
    db_session.add(user)
    db_session.flush()
    assert user.role == UserRole.ADMIN.value
