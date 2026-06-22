"""Full sequential journey regression for all 12 multihop problems."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.seed import seed_problems, seed_solution_paths, seed_solution_steps
from step_engine import build_solution_plan
from tests.evaluation_dataset import EVALUATION_DATASET

MULTIHOP_PROBLEMS = [
    problem for problem in EVALUATION_DATASET if problem["topic"] == "multihop"
]


def _seed_library(db_session: Session) -> None:
    seed_problems(db_session)
    seed_solution_paths(db_session)
    seed_solution_steps(db_session)
    db_session.flush()


def _start(client: TestClient, problem_id: str) -> dict:
    response = client.post("/start-session", json={"problem_id": problem_id})
    assert response.status_code == 200, response.text
    return response.json()


def _submit(client: TestClient, session_id: str, step: str) -> dict:
    response = client.post(
        "/submit-step",
        json={"session_id": session_id, "step": step},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def seeded_db(db_session: Session) -> Session:
    _seed_library(db_session)
    return db_session


@pytest.mark.parametrize(
    "problem",
    MULTIHOP_PROBLEMS,
    ids=[problem["problem_id"] for problem in MULTIHOP_PROBLEMS],
)
def test_multihop_sequential_journey_completes(
    client: TestClient,
    seeded_db: Session,
    problem: dict,
) -> None:
    plan = build_solution_plan(problem["expression"])
    started = _start(client, problem["problem_id"])

    assert started["step_count"] == len(plan.steps)
    assert started["problem_expression"] == problem["expression"]

    for index, step in enumerate(plan.steps):
        result = _submit(client, started["session_id"], step)
        assert result["is_equivalent"] is True, (
            f"{problem['problem_id']} step {index + 1}: {step}"
        )
        if index < len(plan.steps) - 1:
            assert result["session_complete"] is False
        else:
            assert result["session_complete"] is True
            assert result["current_expression"] == plan.final_answer
