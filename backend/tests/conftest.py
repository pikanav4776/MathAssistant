"""Shared pytest fixtures for the MathAssistant backend test suite."""
import pytest

from main import StepValidator


@pytest.fixture
def validator() -> StepValidator:
    return StepValidator()
