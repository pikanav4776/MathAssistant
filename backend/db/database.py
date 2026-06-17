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


def init_db() -> None:
    _require_database()
    import db.models  # noqa: F401 — register ORM tables with Base.metadata

    # Dev convenience: create missing tables on startup. Does not alter existing
    # tables. For schema changes use Alembic (`alembic upgrade head`).
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
