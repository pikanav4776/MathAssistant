"""baseline schema

Revision ID: c09698281fc1
Revises:
Create Date: 2026-06-17 10:41:52.860295

Baseline revision for schema already applied via SQL_edits.sql and prior
migrations. Existing databases should be stamped with this revision
(``alembic stamp head``) rather than running upgrade. Fresh databases can
run ``alembic upgrade head`` after a future revision adds create-table DDL,
or use init_db() create_all for local dev.
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "c09698281fc1"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema already exists in live DB; no-op baseline."""
    pass


def downgrade() -> None:
    """Baseline has no downgrade path."""
    pass
