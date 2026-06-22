"""Password hashing helpers for future register/login endpoints."""

from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt hash suitable for storing in users.password_hash."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True when plain_password matches the stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )
