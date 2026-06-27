"""add school descriptions

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-28

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in sa.inspect(conn).get_columns(table_name))


def upgrade() -> None:
    conn = op.get_bind()
    if not column_exists(conn, "schools", "description"):
        with op.batch_alter_table("schools") as batch_op:
            batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))

    conn.execute(
        sa.text(
            """
            update schools
            set description = :description
            where slug = :slug and description is null
            """
        ),
        {
            "slug": "zhijiang-university",
            "description": "枝江大学是 UTOO 的虚拟公共区，不是真实学校。这里承载公共讨论、跨校交流和未填写学校用户的默认展示。",
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    if column_exists(conn, "schools", "description"):
        with op.batch_alter_table("schools") as batch_op:
            batch_op.drop_column("description")
