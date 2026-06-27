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
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("comments")}
    if "agent_id" not in columns:
        with op.batch_alter_table("comments") as batch_op:
            batch_op.add_column(sa.Column("agent_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key("fk_comments_agent_id_agents", "agents", ["agent_id"], ["id"])


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("comments")}
    if "agent_id" in columns:
        with op.batch_alter_table("comments") as batch_op:
            batch_op.drop_constraint("fk_comments_agent_id_agents", type_="foreignkey")
            batch_op.drop_column("agent_id")
