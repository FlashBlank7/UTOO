"""add moderation controls

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_banned", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("muted_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("posts", sa.Column("visibility", sa.String(20), nullable=False, server_default="normal"))
    op.add_column("comments", sa.Column("visibility", sa.String(20), nullable=False, server_default="normal"))
    op.execute("UPDATE posts SET visibility = 'deleted' WHERE is_deleted = true")
    op.execute("UPDATE comments SET visibility = 'deleted' WHERE is_deleted = true")

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("resolved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "moderation_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reports_target", "reports", ["target_type", "target_id"])
    op.create_index("ix_rate_limit_lookup", "rate_limit_events", ["actor_type", "actor_id", "action", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_rate_limit_lookup", table_name="rate_limit_events")
    op.drop_index("ix_reports_target", table_name="reports")
    op.drop_table("rate_limit_events")
    op.drop_table("moderation_logs")
    op.drop_table("reports")
    op.drop_column("comments", "visibility")
    op.drop_column("posts", "visibility")
    op.drop_column("users", "muted_until")
    op.drop_column("users", "is_banned")
