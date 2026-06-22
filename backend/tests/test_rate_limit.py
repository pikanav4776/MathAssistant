"""Rate limiting and production secret validation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from rate_limit import SlidingWindowLimiter, assert_production_secrets


def test_sliding_window_limiter_blocks_after_limit() -> None:
    limiter = SlidingWindowLimiter()
    key = "test-bucket"
    assert limiter.allow(key, limit=2, window_seconds=60) is True
    assert limiter.allow(key, limit=2, window_seconds=60) is True
    assert limiter.allow(key, limit=2, window_seconds=60) is False


def test_login_rate_limit_returns_429(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    import rate_limit as rate_limit_module

    monkeypatch.setattr(
        rate_limit_module,
        "RATE_LIMITS",
        {("POST", "/auth/login"): (2, 60)},
    )
    rate_limit_module._limiter = SlidingWindowLimiter()

    payload = {"email": "ratelimit@example.com", "password": "wrong-password"}
    assert client.post("/auth/login", json=payload).status_code == 401
    assert client.post("/auth/login", json=payload).status_code == 401
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 429
    assert response.json()["detail"]["error"] == "rate_limit_exceeded"


def test_assert_production_secrets_allows_local_default(monkeypatch) -> None:
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    assert_production_secrets()


def test_assert_production_secrets_rejects_dev_default_on_render(monkeypatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("JWT_SECRET", "dev-secret-change-me-before-production-use")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        assert_production_secrets()


def test_assert_production_secrets_accepts_custom_secret_on_render(monkeypatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("JWT_SECRET", "production-secret-value-12345")
    assert_production_secrets()
