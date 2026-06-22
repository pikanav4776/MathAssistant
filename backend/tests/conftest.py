"""Shared pytest fixtures for the MathAssistant backend test suite."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.database import Base, get_db
from main import app


@pytest.fixture
def validator():
    from main import StepValidator

    return StepValidator()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def test_engine(test_database_url: str):
    connect_args = (
        {"check_same_thread": False} if test_database_url.startswith("sqlite") else {}
    )
    engine = create_engine(test_database_url, connect_args=connect_args)
    import db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session, monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr("main.init_db", lambda: None)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
