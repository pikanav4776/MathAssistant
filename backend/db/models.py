from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


# If upgrading from Phase 6, drop and recreate the problems table or add columns
# manually:
#   ALTER TABLE problems ADD COLUMN IF NOT EXISTS difficulty VARCHAR;
#   ALTER TABLE problems ADD COLUMN IF NOT EXISTS topic VARCHAR;
class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    expression: Mapped[str] = mapped_column(Text, nullable=False)
    expected_final: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String, nullable=True)
    topic: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    sessions: Mapped[list[TutoringSession]] = relationship(back_populates="problem")
    wrong_answers: Mapped[list[ProblemWrongAnswer]] = relationship(
        back_populates="problem"
    )


# If upgrading from Phase 7, add the description column manually:
#   ALTER TABLE problem_wrong_answers ADD COLUMN IF NOT EXISTS description TEXT;
class ProblemWrongAnswer(Base):
    __tablename__ = "problem_wrong_answers"
    __table_args__ = (
        UniqueConstraint("problem_id", "wrong_step", name="uq_problem_wrong_step"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("problems.id"), nullable=False
    )
    wrong_step: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    problem: Mapped[Problem] = relationship(back_populates="wrong_answers")


class TutoringSession(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("problems.id"), nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hint_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    problem: Mapped[Problem] = relationship(back_populates="sessions")
    attempts: Mapped[list[Attempt]] = relationship(back_populates="session")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("sessions.session_id"), nullable=False
    )
    step: Mapped[str] = mapped_column(Text, nullable=False)
    expected: Mapped[str] = mapped_column(Text, nullable=False)
    is_equivalent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[str | None] = mapped_column(String, nullable=True)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    session: Mapped[TutoringSession] = relationship(back_populates="attempts")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
