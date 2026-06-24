"""add user display name

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(50), nullable=True))
    op.execute("UPDATE users SET display_name = username WHERE display_name IS NULL AND username IS NOT NULL")


def downgrade() -> None:
    op.drop_column("users", "display_name")
