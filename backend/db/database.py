from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")


def _normalize_database_url(url: str) -> str:
    """Accept postgres:// URLs (Neon, Heroku) and normalize for SQLAlchemy."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


_raw_database_url = os.environ.get("DATABASE_URL")
DATABASE_URL = _normalize_database_url(_raw_database_url) if _raw_database_url else None

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)
Base = declarative_base()


def _require_database() -> None:
    if engine is None or SessionLocal is None:
        raise ValueError(
            "DATABASE_URL environment variable is required "
            "(e.g. postgresql://user:password@host/db?sslmode=require for Neon)"
        )


def _is_local_database_url(url: str | None) -> bool:
    if not url:
        return False
    lowered = url.lower()
    return any(
        host in lowered
        for host in ("localhost", "127.0.0.1", "@host.docker.internal")
    )


def _should_use_create_all() -> bool:
    """Use SQLAlchemy create_all only for local development convenience."""
    environment = os.environ.get("ENVIRONMENT", "").strip().lower()
    if environment == "development":
        return True

    skip_migrations = os.environ.get("SKIP_MIGRATIONS", "").strip().lower()
    if skip_migrations in {"1", "true", "yes"}:
        return True

    return _is_local_database_url(_raw_database_url) or _is_local_database_url(
        DATABASE_URL
    )


def check_db_connection() -> bool:
    """Return True when the database accepts a simple query."""
    _require_database()
    db = SessionLocal()
    try:
        db.connection().exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False
    finally:
        db.close()


def init_db() -> None:
    _require_database()
    import db.models  # noqa: F401 — register ORM tables with Base.metadata

    if _should_use_create_all():
        # Local dev only: create missing tables on startup. Does not alter existing
        # tables. Production schema is applied via `alembic upgrade head`.
        Base.metadata.create_all(bind=engine)

    from db.seed import seed_problems, seed_wrong_answers

    db = SessionLocal()
    try:
        seed_problems(db)
        seed_wrong_answers(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    _require_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
