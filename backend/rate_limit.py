"""In-memory sliding-window rate limiting for hot API endpoints."""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

_DEV_JWT_SECRET = "dev-secret-change-me-before-production-use"

# (method, path) -> (max_requests, window_seconds)
RATE_LIMITS: dict[tuple[str, str], tuple[int, int]] = {
    ("POST", "/auth/login"): (10, 60),
    ("POST", "/auth/register"): (5, 60),
    ("POST", "/start-session"): (30, 60),
    ("POST", "/submit-step"): (120, 60),
}


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            recent = [timestamp for timestamp in self._events[key] if timestamp > cutoff]
            if len(recent) >= limit:
                self._events[key] = recent
                return False
            recent.append(now)
            self._events[key] = recent
            return True


_limiter = SlidingWindowLimiter()


def rate_limit_enabled() -> bool:
    raw = os.environ.get("RATE_LIMIT_ENABLED", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not rate_limit_enabled():
            return await call_next(request)

        rule = RATE_LIMITS.get((request.method, request.url.path))
        if rule is None:
            return await call_next(request)

        limit, window_seconds = rule
        bucket_key = f"{request.method}:{request.url.path}:{client_ip(request)}"
        if _limiter.allow(bucket_key, limit, window_seconds):
            return await call_next(request)

        return JSONResponse(
            status_code=429,
            content={
                "detail": {
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please wait and try again.",
                }
            },
        )


def is_render_deploy() -> bool:
    return os.environ.get("RENDER", "").strip().lower() == "true"


def assert_production_secrets() -> None:
    """Fail fast on Render when JWT_SECRET is missing or still the dev default."""
    if not is_render_deploy():
        return

    jwt_secret = os.environ.get("JWT_SECRET", "").strip()
    if not jwt_secret or jwt_secret == _DEV_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET must be set to a strong random value on Render. "
            "The development default is not allowed in deployed environments."
        )
