from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


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
    solution_paths: Mapped[list[SolutionPath]] = relationship(
        back_populates="problem"
    )
    session_summaries: Mapped[list[SessionSummary]] = relationship(
        back_populates="problem"
    )


class SolutionPath(Base):
    __tablename__ = "solution_paths"

    sol_path_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    sol_path_name: Mapped[str] = mapped_column(
        String, nullable=False, server_default="default"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    problem: Mapped[Problem] = relationship(back_populates="solution_paths")
    steps: Mapped[list[SolutionStep]] = relationship(back_populates="path")


class SolutionStep(Base):
    __tablename__ = "solution_steps"
    __table_args__ = (
        UniqueConstraint("path_id", "step_order", name="uq_solution_steps_path_order"),
        Index("ix_solution_steps_path_id", "path_id"),
    )

    sol_step_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    path_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("solution_paths.sol_path_id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sol_step_expression: Mapped[str] = mapped_column(Text, nullable=False)
    hint_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    path: Mapped[SolutionPath] = relationship(back_populates="steps")
    sessions_at_step: Mapped[list[TutoringSession]] = relationship(
        back_populates="current_step"
    )
    wrong_answers: Mapped[list[ProblemWrongAnswer]] = relationship(
        back_populates="solution_step"
    )


class ProblemWrongAnswer(Base):
    __tablename__ = "problem_wrong_answers"
    __table_args__ = (
        UniqueConstraint("problem_id", "wrong_step", name="uq_problem_wrong_step"),
        Index("ix_pwa_solution_step_id", "solution_step_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("problems.id"), nullable=False
    )
    wrong_step: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_step_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("solution_steps.sol_step_id"), nullable=True
    )

    problem: Mapped[Problem] = relationship(back_populates="wrong_answers")
    solution_step: Mapped[SolutionStep | None] = relationship(
        back_populates="wrong_answers"
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("uq_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False, server_default="student")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    sessions: Mapped[list[TutoringSession]] = relationship(back_populates="user")
    session_summaries: Mapped[list[SessionSummary]] = relationship(
        back_populates="user"
    )


class TutoringSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_current_step_id", "current_step_id"),
    )

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("problems.id"), nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_attempt_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    hint_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    current_step_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("solution_steps.sol_step_id"), nullable=True
    )

    problem: Mapped[Problem] = relationship(back_populates="sessions")
    user: Mapped[User | None] = relationship(back_populates="sessions")
    current_step: Mapped[SolutionStep | None] = relationship(
        back_populates="sessions_at_step"
    )
    attempts: Mapped[list[Attempt]] = relationship(back_populates="session")
    summary: Mapped[SessionSummary | None] = relationship(
        back_populates="session", uselist=False
    )


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


class SessionSummary(Base):
    __tablename__ = "session_summaries"
    __table_args__ = (
        Index("ix_session_summaries_problem_id", "problem_id"),
        Index("ix_session_summaries_user_id", "user_id"),
    )

    session_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("problems.id"), nullable=False
    )
    total_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    incorrect_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    revealed_solution: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_error_type: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[TutoringSession] = relationship(back_populates="summary")
    user: Mapped[User | None] = relationship(back_populates="session_summaries")
    problem: Mapped[Problem] = relationship(back_populates="session_summaries")


class DailyProblemStats(Base):
    __tablename__ = "daily_problem_stats"

    stat_date: Mapped[date] = mapped_column(Date, primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("problems.id"), primary_key=True
    )
    sessions_started: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    sessions_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    avg_attempts: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    top_error_type: Mapped[str | None] = mapped_column(String, nullable=True)


class DailyErrorStats(Base):
    __tablename__ = "daily_error_stats"

    stat_date: Mapped[date] = mapped_column(Date, primary_key=True)
    error_type: Mapped[str] = mapped_column(String, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
