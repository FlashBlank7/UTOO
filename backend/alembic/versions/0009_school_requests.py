"""add school requests

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-27

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table_name: str) -> bool:
    return sa.inspect(conn).has_table(table_name)


def upgrade() -> None:
    conn = op.get_bind()
    if table_exists(conn, "school_requests"):
        return

    op.create_table(
        "school_requests",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name_zh", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("name_ja", sa.String(length=200), nullable=True),
        sa.Column("aliases", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=300), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    conn = op.get_bind()
    if table_exists(conn, "school_requests"):
        op.drop_table("school_requests")
