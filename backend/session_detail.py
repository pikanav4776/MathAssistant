"""Helpers for enriching session GET responses."""

from __future__ import annotations

from db.models import SolutionStep, TutoringSession


def step_index_for_session(session_row: TutoringSession, steps: list[SolutionStep]) -> int:
    if not steps:
        return 1
    if session_row.completed:
        return len(steps)
    if session_row.current_step_id is None:
        return 1
    for index, row in enumerate(steps):
        if row.sol_step_id == session_row.current_step_id:
            return index + 1
    return 1