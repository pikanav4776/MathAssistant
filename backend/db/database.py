from __future__ import annotations

import json
import os
import time
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# #region agent log
_DEBUG_LOG = Path(__file__).resolve().parent.parent.parent / "debug-7ef75b.log"


def _agent_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    try:
        with _DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "sessionId": "7ef75b",
                        "hypothesisId": hypothesis_id,
                        "location": location,
                        "message": message,
                        "data": data,
                        "timestamp": int(time.time() * 1000),
                    }
                )
                + "\n"
            )
    except OSError:
        pass


# #endregion

_backend_dir = Path(__file__).resolve().parent.parent
_dotenv_path = _backend_dir / ".env"
_dotenv_loaded = load_dotenv(_dotenv_path)
# #region agent log
_agent_log(
    "A",
    "database.py:load_dotenv",
    "dotenv load attempt",
    {
        "cwd": os.getcwd(),
        "dotenv_path": str(_dotenv_path),
        "dotenv_exists": _dotenv_path.is_file(),
        "dotenv_example_exists": (_backend_dir / ".env.example").is_file(),
        "load_dotenv_returned": _dotenv_loaded,
    },
)
# #endregion

DATABASE_URL = os.environ.get("DATABASE_URL")
# #region agent log
_agent_log(
    "B",
    "database.py:DATABASE_URL",
    "env var resolution",
    {
        "database_url_set": DATABASE_URL is not None,
        "database_url_length": len(DATABASE_URL) if DATABASE_URL else 0,
        "env_has_database_url_key": "DATABASE_URL" in os.environ,
    },
)
# #endregion

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)
Base = declarative_base()


def _require_database() -> None:
    if engine is None or SessionLocal is None:
        # #region agent log
        _agent_log(
            "C",
            "database.py:_require_database",
            "database unavailable at require",
            {
                "engine_is_none": engine is None,
                "session_local_is_none": SessionLocal is None,
                "dotenv_path": str(_dotenv_path),
                "dotenv_exists": _dotenv_path.is_file(),
            },
        )
        # #endregion
        raise ValueError(
            "DATABASE_URL environment variable is required "
            "(e.g. postgresql://user:password@localhost:5433/mathassistant)"
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
