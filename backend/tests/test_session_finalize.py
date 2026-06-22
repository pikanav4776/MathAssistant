"""HTTP integration tests for session finalize, history, and resume fields."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.models import SessionSummary as SessionSummaryRecord, TutoringSession


def _register(client: TestClient, email: str, password: str = "password123") -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _start_session(client: TestClient, token: str | None = None) -> str:
    headers = _auth_headers(token) if token else {}
    response = client.post(
        "/start-session",
        json={"problem_expression": "2(x+3)"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def test_finalize_solved_creates_session_summary(
    client: TestClient, db_session: Session
) -> None:
    reg = _register(client, "finalize_solved@example.com")
    token = reg["access_token"]
    session_id = _start_session(client, token)

    submit = client.post(
        "/submit-step",
        json={"session_id": session_id, "step": "2*x + 6"},
        headers=_auth_headers(token),
    )
    assert submit.status_code == 200

    finalize = client.post(
        f"/session/{session_id}/finalize",
        json={"completed": True, "revealed_solution": False},
        headers=_auth_headers(token),
    )
    assert finalize.status_code == 200
    assert finalize.json()["summarized"] is True

    summary = (
        db_session.query(SessionSummaryRecord)
        .filter_by(session_id=session_id)
        .one()
    )
    assert summary.completed is True
    assert summary.revealed_solution is False
    assert summary.total_attempts >= 1

    session_row = (
        db_session.query(TutoringSession).filter_by(session_id=session_id).one()
    )
    assert session_row.completed is True


def test_finalize_give_up_sets_revealed_solution(
    client: TestClient, db_session: Session
) -> None:
    reg = _register(client, "finalize_giveup@example.com")
    token = reg["access_token"]
    session_id = _start_session(client, token)

    finalize = client.post(
        f"/session/{session_id}/finalize",
        json={"completed": False, "revealed_solution": True},
        headers=_auth_headers(token),
    )
    assert finalize.status_code == 200

    summary = (
        db_session.query(SessionSummaryRecord)
        .filter_by(session_id=session_id)
        .one()
    )
    assert summary.completed is False
    assert summary.revealed_solution is True


def test_user_session_history_returns_finalized_sessions(client: TestClient) -> None:
    reg = _register(client, "history_user@example.com")
    token = reg["access_token"]
    session_id = _start_session(client, token)

    client.post(
        f"/session/{session_id}/finalize",
        json={"completed": True, "revealed_solution": False},
        headers=_auth_headers(token),
    )

    history = client.get("/auth/me/sessions", headers=_auth_headers(token))
    assert history.status_code == 200
    items = history.json()
    assert len(items) >= 1
    assert items[0]["session_id"] == session_id
    assert items[0]["completed"] is True


def test_user_session_history_requires_auth(client: TestClient) -> None:
    response = client.get("/auth/me/sessions")
    assert response.status_code == 401


def test_get_session_includes_resume_fields(client: TestClient) -> None:
    session_id = _start_session(client)

    response = client.get(f"/session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["step_index"] >= 1
    assert data["step_count"] >= 1
    assert "expected_final" in data
    assert "incorrect_attempt_count" in data
    assert data["topic"] is not None


def test_owned_session_finalize_requires_auth(client: TestClient) -> None:
    reg = _register(client, "finalize_auth@example.com")
    token = reg["access_token"]
    session_id = _start_session(client, token)

    denied = client.post(
        f"/session/{session_id}/finalize",
        json={"completed": True, "revealed_solution": False},
    )
    assert denied.status_code == 401

    allowed = client.post(
        f"/session/{session_id}/finalize",
        json={"completed": True, "revealed_solution": False},
        headers=_auth_headers(token),
    )
    assert allowed.status_code == 200
