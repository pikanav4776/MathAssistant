"""Authentication utilities (password hashing, JWT) and API routes."""

from auth.auth_utils import hash_password, verify_password
from auth.deps import get_current_user, get_optional_user, require_admin
from auth.jwt_utils import create_token, decode_token
from auth.routes import router as auth_router

__all__ = [
    "hash_password",
    "verify_password",
    "create_token",
    "decode_token",
    "get_current_user",
    "get_optional_user",
    "require_admin",
    "auth_router",
]