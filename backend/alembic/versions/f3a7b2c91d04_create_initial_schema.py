"""create initial schema

Revision ID: f3a7b2c91d04
Revises: c09698281fc1
Create Date: 2026-06-17 12:00:00.000000

Creates all tables defined in backend/db/models.py for fresh databases.
Existing production databases that already have this schema should be stamped
with ``alembic stamp head`` (one-time) instead of running this upgrade.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a7b2c91d04"
down_revision: Union[str, Sequence[str], None] = "c09698281fc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "problems",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("expression", sa.Text(), nullable=False),
        sa.Column("expected_final", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=True),
        sa.Column("topic", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column(
            "role", sa.String(), server_default="student", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_users_email", "users", ["email"], unique=True)
    op.create_table(
        "daily_error_stats",
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("error_type", sa.String(), nullable=False),
        sa.Column(
            "count", sa.Integer(), server_default="0", nullable=False
        ),
        sa.PrimaryKeyConstraint("stat_date", "error_type"),
    )
    op.create_table(
        "daily_problem_stats",
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("problem_id", sa.String(), nullable=False),
        sa.Column(
            "sessions_started", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "sessions_completed", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column("avg_attempts", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("top_error_type", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.PrimaryKeyConstraint("stat_date", "problem_id"),
    )
    op.create_table(
        "solution_paths",
        sa.Column("sol_path_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("problem_id", sa.String(), nullable=False),
        sa.Column(
            "sol_path_name", sa.String(), server_default="default", nullable=False
        ),
        sa.Column(
            "is_primary", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"], ["problems.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("sol_path_id"),
    )
    op.create_table(
        "solution_steps",
        sa.Column("sol_step_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("path_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("sol_step_expression", sa.Text(), nullable=False),
        sa.Column("hint_template", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["path_id"], ["solution_paths.sol_path_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("sol_step_id"),
        sa.UniqueConstraint("path_id", "step_order", name="uq_solution_steps_path_order"),
    )
    op.create_index("ix_solution_steps_path_id", "solution_steps", ["path_id"])
    op.create_table(
        "problem_wrong_answers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("problem_id", sa.String(), nullable=False),
        sa.Column("wrong_step", sa.Text(), nullable=False),
        sa.Column("error_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("solution_step_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["solution_step_id"], ["solution_steps.sol_step_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_id", "wrong_step", name="uq_problem_wrong_step"),
    )
    op.create_index(
        "ix_pwa_solution_step_id", "problem_wrong_answers", ["solution_step_id"]
    )
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("problem_id", sa.String(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("incorrect_attempt_count", sa.Integer(), nullable=False),
        sa.Column("hint_level", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_active",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("current_step_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["current_step_id"], ["solution_steps.sol_step_id"]),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_sessions_current_step_id", "sessions", ["current_step_id"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("step", sa.Text(), nullable=False),
        sa.Column("expected", sa.Text(), nullable=False),
        sa.Column("is_equivalent", sa.Boolean(), nullable=False),
        sa.Column("error_type", sa.String(), nullable=True),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "session_summaries",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("problem_id", sa.String(), nullable=False),
        sa.Column(
            "total_attempts", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "incorrect_attempts", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "completed", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column(
            "revealed_solution", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("final_error_type", sa.String(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(
        "ix_session_summaries_problem_id", "session_summaries", ["problem_id"]
    )
    op.create_index(
        "ix_session_summaries_user_id", "session_summaries", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_session_summaries_user_id", table_name="session_summaries")
    op.drop_index("ix_session_summaries_problem_id", table_name="session_summaries")
    op.drop_table("session_summaries")
    op.drop_table("attempts")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_index("ix_sessions_current_step_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_pwa_solution_step_id", table_name="problem_wrong_answers")
    op.drop_table("problem_wrong_answers")
    op.drop_index("ix_solution_steps_path_id", table_name="solution_steps")
    op.drop_table("solution_steps")
    op.drop_table("solution_paths")
    op.drop_table("daily_problem_stats")
    op.drop_table("daily_error_stats")
    op.drop_index("uq_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("problems")
