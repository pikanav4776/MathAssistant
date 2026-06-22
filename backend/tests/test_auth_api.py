"""HTTP integration tests for auth endpoints and session ownership."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from auth.auth_utils import hash_password
from db.models import TutoringSession, User, UserRole


def _register(client: TestClient, email: str, password: str = "password123") -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_me(client: TestClient) -> None:
    reg = _register(client, "auth_user@example.com")
    assert reg["token_type"] == "bearer"
    assert reg["user"]["email"] == "auth_user@example.com"

    login = client.post(
        "/auth/login",
        json={"email": "auth_user@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers=_auth_headers(token))
    assert me.status_code == 200
    assert me.json()["email"] == "auth_user@example.com"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    _register(client, "dup_auth@example.com")
    response = client.post(
        "/auth/register",
        json={"email": "dup_auth@example.com", "password": "password123"},
    )
    assert response.status_code == 409


def test_login_invalid_password_returns_401(client: TestClient) -> None:
    _register(client, "bad_login@example.com")
    response = client.post(
        "/auth/login",
        json={"email": "bad_login@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_start_session_attaches_user_id_when_authenticated(client: TestClient, db_session: Session) -> None:
    reg = _register(client, "session_owner@example.com")
    token = reg["access_token"]

    start = client.post(
        "/start-session",
        json={"problem_expression": "2(x+3)"},
        headers=_auth_headers(token),
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    row = db_session.query(TutoringSession).filter_by(session_id=session_id).one()
    assert row.user_id is not None


def test_owned_session_requires_auth_for_get(client: TestClient, db_session: Session) -> None:
    reg = _register(client, "owner@example.com")
    token = reg["access_token"]
    start = client.post(
        "/start-session",
        json={"problem_expression": "2(x+3)"},
        headers=_auth_headers(token),
    )
    session_id = start.json()["session_id"]

    denied = client.get(f"/session/{session_id}")
    assert denied.status_code == 401

    allowed = client.get(f"/session/{session_id}", headers=_auth_headers(token))
    assert allowed.status_code == 200
    assert allowed.json()["session_id"] == session_id


def test_guest_session_still_accessible_without_auth(client: TestClient) -> None:
    start = client.post("/start-session", json={"problem_expression": "2(x+3)"})
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    response = client.get(f"/session/{session_id}")
    assert response.status_code == 200


def test_create_problem_requires_admin(client: TestClient, db_session: Session) -> None:
    reg = _register(client, "regular@example.com")
    token = reg["access_token"]

    denied = client.post(
        "/problem",
        json={
            "id": "auth_test_prob",
            "expression": "x+1",
            "expected_final": "x+1",
        },
        headers=_auth_headers(token),
    )
    assert denied.status_code == 403

    admin = User(
        email="admin_auth@example.com",
        password_hash=hash_password("admin-pass"),
        role=UserRole.ADMIN.value,
    )
    db_session.add(admin)
    db_session.flush()

    from auth.jwt_utils import create_token

    admin_token = create_token(admin.id, admin.role)
    allowed = client.post(
        "/problem",
        json={
            "id": "auth_test_prob",
            "expression": "x+1",
            "expected_final": "x+1",
        },
        headers=_auth_headers(admin_token),
    )
    assert allowed.status_code == 201