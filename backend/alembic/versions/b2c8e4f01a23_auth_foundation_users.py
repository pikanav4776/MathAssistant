"""create users table with auth foundation

Revision ID: b2c8e4f01a23
Revises: a41b7d2e9c10
Create Date: 2026-06-19 12:00:00.000000

Creates users when missing (drifted DBs) or aligns role default/CHECK on existing
tables. Migrates legacy ``student`` role values to ``user``.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c8e4f01a23"
down_revision: Union[str, Sequence[str], None] = "a41b7d2e9c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _users_table_exists(bind: sa.engine.Connection) -> bool:
    return "users" in sa.inspect(bind).get_table_names()


def _users_role_check_exists(bind: sa.engine.Connection) -> bool:
    inspector = sa.inspect(bind)
    return any(
        constraint.get("name") == "ck_users_role"
        for constraint in inspector.get_check_constraints("users")
    )


def upgrade() -> None:
    bind = op.get_bind()

    if not _users_table_exists(bind):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.Column("display_name", sa.String(), nullable=True),
            sa.Column(
                "role", sa.String(), server_default="user", nullable=False
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "role IN ('user', 'admin')", name="ck_users_role"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("uq_users_email", "users", ["email"], unique=True)
        return

    op.execute("UPDATE users SET role = 'user' WHERE role = 'student'")
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(),
        server_default="user",
        existing_nullable=False,
    )
    if not _users_role_check_exists(bind):
        op.create_check_constraint(
            "ck_users_role",
            "users",
            "role IN ('user', 'admin')",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if not _users_table_exists(bind):
        return

    if _users_role_check_exists(bind):
        op.drop_constraint("ck_users_role", "users", type_="check")
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(),
        server_default="student",
        existing_nullable=False,
    )
