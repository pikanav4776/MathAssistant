"""v0.3 session state columns

Revision ID: a41b7d2e9c10
Revises: f3a7b2c91d04
Create Date: 2026-06-18 08:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a41b7d2e9c10"
down_revision: Union[str, Sequence[str], None] = "f3a7b2c91d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("current_expression", sa.Text(), nullable=True),
    )
    op.add_column(
        "sessions",
        sa.Column(
            "completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "attempts",
        sa.Column(
            "step_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )

    op.execute(
        """
        UPDATE sessions s
        SET current_expression = p.expression
        FROM problems p
        WHERE s.problem_id = p.id
        """
    )
    op.execute(
        """
        UPDATE sessions
        SET current_expression = ''
        WHERE current_expression IS NULL
        """
    )

    op.alter_column("sessions", "current_expression", nullable=False)

    op.alter_column("sessions", "completed", server_default=None)
    op.alter_column("attempts", "step_order", server_default=None)


def downgrade() -> None:
    op.drop_column("attempts", "step_order")
    op.drop_column("sessions", "completed")
    op.drop_column("sessions", "current_expression")
