"""add forum content controls

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("category", sa.String(20), nullable=False, server_default="闲聊"))
    op.add_column("posts", sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("posts", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("posts", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("comments", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("comments", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("comments", "deleted_at")
    op.drop_column("comments", "is_deleted")
    op.drop_column("posts", "deleted_at")
    op.drop_column("posts", "is_deleted")
    op.drop_column("posts", "is_pinned")
    op.drop_column("posts", "category")
