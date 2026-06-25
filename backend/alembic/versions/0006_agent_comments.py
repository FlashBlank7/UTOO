"""allow agent comments

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("comments") as batch_op:
        batch_op.add_column(sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True))
        batch_op.alter_column("author_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("comments") as batch_op:
        batch_op.alter_column("author_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("agent_id")
