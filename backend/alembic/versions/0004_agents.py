"""add agent posting

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(80), unique=True, nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("api_key_prefix", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("api_key_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_posted_at", sa.DateTime(timezone=True), nullable=True),
    )

    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("agent_id", sa.Integer(), nullable=True))
        batch_op.alter_column("author_id", existing_type=sa.Integer(), nullable=True)
        batch_op.create_foreign_key("fk_posts_agent_id_agents", "agents", ["agent_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_constraint("fk_posts_agent_id_agents", type_="foreignkey")
        batch_op.alter_column("author_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("agent_id")

    op.drop_table("agents")
