"""Tests for starter problems API and POST /problem validation."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from auth.auth_utils import hash_password
from db.models import User, UserRole
from db.seed import seed_problems
from db.starter_problems import STARTER_PROBLEM_IDS


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(db_session: Session) -> str:
    admin = User(
        email="problem_admin@example.com",
        password_hash=hash_password("admin-pass"),
        role=UserRole.ADMIN.value,
    )
    db_session.add(admin)
    db_session.flush()
    from auth.jwt_utils import create_token

    return create_token(admin.id, admin.role)


def test_list_starter_problems(client: TestClient, db_session: Session) -> None:
    seed_problems(db_session)
    db_session.flush()

    response = client.get("/problems/starter")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == len(STARTER_PROBLEM_IDS)
    assert items[0]["id"] == STARTER_PROBLEM_IDS[0]


def test_list_starter_problems_filter_by_topic(client: TestClient, db_session: Session) -> None:
    seed_problems(db_session)
    db_session.flush()

    response = client.get("/problems/starter", params={"topic": "multihop"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 3
    assert all(item["topic"] == "multihop" for item in items)


def test_list_starter_problems_filter_empty_returns_404(
    client: TestClient, db_session: Session
) -> None:
    seed_problems(db_session)
    db_session.flush()

    response = client.get("/problems/starter", params={"difficulty": "hard", "topic": "distribution"})
    assert response.status_code == 404


def test_create_problem_rejects_unsupported_expression(
    client: TestClient, db_session: Session
) -> None:
    token = _admin_token(db_session)
    response = client.post(
        "/problem",
        json={
            "id": "bad_prob_sqrt",
            "expression": "sqrt(x)",
            "expected_final": "sqrt(x)",
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "unsupported_problem"


def test_create_problem_rejects_expected_final_mismatch(
    client: TestClient, db_session: Session
) -> None:
    token = _admin_token(db_session)
    response = client.post(
        "/problem",
        json={
            "id": "bad_prob_final",
            "expression": "2(x+3)",
            "expected_final": "2x+9",
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "expected_final_mismatch"


def test_create_problem_stores_engine_canonical_final(
    client: TestClient, db_session: Session
) -> None:
    token = _admin_token(db_session)
    response = client.post(
        "/problem",
        json={
            "id": "canonical_prob",
            "expression": "x+3-2x+1",
            "expected_final": "4-x",
            "difficulty": "easy",
            "topic": "simplification",
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["expected_final"] == "4-x"
