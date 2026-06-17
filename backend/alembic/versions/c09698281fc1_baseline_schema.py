"""baseline schema

Revision ID: c09698281fc1
Revises:
Create Date: 2026-06-17 10:41:52.860295

Baseline revision for databases that already had schema applied via SQL_edits.sql,
create_all(), or manual DDL. Existing databases should be stamped with
``alembic stamp head`` (one-time) rather than running upgrade on the create-table
revision. Fresh databases run ``alembic upgrade head`` to apply f3a7b2c91d04.
Local dev may still use init_db() create_all when ENVIRONMENT=development,
SKIP_MIGRATIONS=true, or DATABASE_URL points at localhost.
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
