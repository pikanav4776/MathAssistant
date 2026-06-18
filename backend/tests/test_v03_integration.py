"""v0.3 full session journey integration tests (start → steps → complete)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.models import TutoringSession
from db.seed import seed_problems, seed_solution_paths, seed_solution_steps
from step_engine import build_solution_plan


def _seed_library(db_session: Session) -> None:
    seed_problems(db_session)
    seed_solution_paths(db_session)
    seed_solution_steps(db_session)
    db_session.flush()


def _start(client: TestClient, problem_id: str) -> dict:
    response = client.post("/start-session", json={"problem_id": problem_id})
    assert response.status_code == 200
    return response.json()


def _submit(client: TestClient, session_id: str, step: str) -> dict:
    response = client.post(
        "/submit-step",
        json={"session_id": session_id, "step": step},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def seeded_db(db_session: Session) -> Session:
    _seed_library(db_session)
    return db_session


def test_full_multihop_journey_sequential(
    client: TestClient, seeded_db: Session
) -> None:
    plan = build_solution_plan("2(x+3)+4")
    started = _start(client, "mhop_001")

    assert started["step_count"] == len(plan.steps)
    assert started["problem_expression"] == "2(x+3)+4"
    assert started["current_expression"] == "2(x+3)+4"

    first = _submit(client, started["session_id"], plan.steps[0])
    assert first["is_equivalent"] is True
    assert first["session_complete"] is False
    assert first["step_index"] == 1
    assert first["current_expression"] == plan.steps[0]

    second = _submit(client, started["session_id"], plan.steps[1])
    assert second["is_equivalent"] is True
    assert second["session_complete"] is True
    assert second["step_index"] == 2
    assert second["current_expression"] == plan.final_answer

    summary = client.get(f"/session/{started['session_id']}")
    assert summary.status_code == 200
    body = summary.json()
    assert body["completed"] is True
    assert body["current_expression"] == plan.final_answer
    assert len(body["attempt_history"]) == 2
    assert all(attempt["is_equivalent"] for attempt in body["attempt_history"])


def test_full_multihop_journey_skip_ahead(
    client: TestClient, seeded_db: Session
) -> None:
    plan = build_solution_plan("3(x-2)+5")
    started = _start(client, "mhop_002")
    result = _submit(client, started["session_id"], plan.final_answer)

    assert result["is_equivalent"] is True
    assert result["session_complete"] is True
    assert result["skip_message"] is not None
    assert result["skipped_steps"] == [
        {"step_order": 1, "expected": plan.steps[0]},
    ]

    row = seeded_db.query(TutoringSession).filter_by(session_id=started["session_id"]).one()
    assert row.completed is True
    assert row.current_expression == plan.final_answer


def test_term_reorder_journey_does_not_advance(
    client: TestClient, seeded_db: Session
) -> None:
    expression = "(8x+6x^2+2)(8x^2+22x+19)"
    plan = build_solution_plan(expression)
    started = _start(client, "mhop_012")
    assert started["step_count"] == 2

    reordered = "(8x^2+22x+19)(8x+6x^2+2)"
    result = _submit(client, started["session_id"], reordered)

    assert result["is_equivalent"] is False
    assert result["error_classification"]["error_type"] == "term_reorder"
    assert result["current_expression"] == expression
    assert result["expected_step"] == plan.steps[0]

    row = seeded_db.query(TutoringSession).filter_by(session_id=started["session_id"]).one()
    assert row.completed is False
    assert row.current_expression == expression
    assert row.incorrect_attempt_count == 0


def test_hint_reveals_solution_after_five_wrong_attempts(
    client: TestClient, seeded_db: Session
) -> None:
    plan = build_solution_plan("5(x+2)-3")
    started = _start(client, "mhop_005")

    for _ in range(5):
        result = _submit(client, started["session_id"], "5x+8")
        assert result["is_equivalent"] is False

    assert "Solution:" in result["hint"]
    assert plan.final_answer in result["hint"]

    row = seeded_db.query(TutoringSession).filter_by(session_id=started["session_id"]).one()
    assert row.completed is False
    assert row.incorrect_attempt_count == 5


def test_inline_expression_journey_completes(
    client: TestClient, seeded_db: Session
) -> None:
    expression = "(x+1)(x+2)+3"
    plan = build_solution_plan(expression)
    response = client.post("/start-session", json={"problem_expression": expression})
    assert response.status_code == 200
    started = response.json()
    assert started["step_count"] == len(plan.steps)

    for step in plan.steps[:-1]:
        partial = _submit(client, started["session_id"], step)
        assert partial["session_complete"] is False

    final = _submit(client, started["session_id"], plan.steps[-1])
    assert final["session_complete"] is True
    assert final["current_expression"] == plan.final_answer
