"""make user department optional

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("department", existing_type=sa.String(length=100), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE users SET department = '' WHERE department IS NULL")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("department", existing_type=sa.String(length=100), nullable=False)
