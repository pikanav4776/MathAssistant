"""v0.3 API integration tests — session flow, skip-ahead, and validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from session_helpers import seed_problem_with_plan, start_tutoring_session
from db.models import TutoringSession


def _submit(client: TestClient, session_id: str, step: str) -> dict:
    response = client.post(
        "/submit-step",
        json={"session_id": session_id, "step": step},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def multihop_session(db_session: Session) -> tuple[TutoringSession, list]:
    problem, steps = seed_problem_with_plan(db_session, "2(x+3)+4")
    session = start_tutoring_session(db_session, problem, steps)
    db_session.commit()
    return session, steps


def test_start_session_via_problem_id(client: TestClient, db_session: Session) -> None:
    problem, _ = seed_problem_with_plan(db_session, "2(x+3)", problem_id="api_dist_001")
    db_session.commit()

    response = client.post("/start-session", json={"problem_id": problem.id})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["problem_expression"] == "2(x+3)"
    assert body["step_count"] == 1


def test_skip_ahead_to_step_two_accepted(
    client: TestClient, multihop_session: tuple[TutoringSession, list]
) -> None:
    session, steps = multihop_session
    result = _submit(client, session.session_id, steps[1].sol_step_expression)

    assert result["is_equivalent"] is True
    assert result["session_complete"] is True
    assert result["skip_message"] == (
        "You skipped step 1 (expected: 2x+6+4). Continuing from your answer."
    )
    assert result["skipped_steps"] == [
        {"step_order": 1, "expected": "2x+6+4"},
    ]


def test_wrong_skip_attempt_validates_against_immediate_expected(
    client: TestClient, multihop_session: tuple[TutoringSession, list]
) -> None:
    session, steps = multihop_session
    result = _submit(client, session.session_id, "2x+12")

    assert result["is_equivalent"] is False
    assert result["expected_step"] == steps[0].sol_step_expression
    assert result.get("skip_message") is None


def test_sequential_steps_still_work(
    client: TestClient, multihop_session: tuple[TutoringSession, list]
) -> None:
    session, steps = multihop_session

    first = _submit(client, session.session_id, steps[0].sol_step_expression)
    assert first["is_equivalent"] is True
    assert first.get("skip_message") is None
    assert first["session_complete"] is False
    assert first["step_index"] == 1

    second = _submit(client, session.session_id, steps[1].sol_step_expression)
    assert second["is_equivalent"] is True
    assert second["session_complete"] is True
    assert second.get("skip_message") is None


def test_no_progress_rejected(client: TestClient, multihop_session) -> None:
    session, _ = multihop_session
    result = _submit(client, session.session_id, "2(x+3)+4")

    assert result["is_equivalent"] is False
    assert result["error_classification"]["error_type"] == "no_progress"


def test_skip_to_final_single_hop(
    client: TestClient, db_session: Session
) -> None:
    problem, steps = seed_problem_with_plan(db_session, "2(x+3)", problem_id="api_skip_final")
    session = start_tutoring_session(db_session, problem, steps)
    db_session.commit()

    result = _submit(client, session.session_id, steps[0].sol_step_expression)
    assert result["is_equivalent"] is True
    assert result["session_complete"] is True
    assert result.get("skip_message") is None


def test_first_step_wrong(
    client: TestClient,
    db_session: Session,
    multihop_session: tuple[TutoringSession, list],
) -> None:
    session, steps = multihop_session
    result = _submit(client, session.session_id, "2x+6")

    assert result["is_equivalent"] is False
    assert result["expected_step"] == steps[0].sol_step_expression

    row = db_session.query(TutoringSession).filter_by(session_id=session.session_id).one()
    assert row.completed is False
    assert row.current_step_id is None
