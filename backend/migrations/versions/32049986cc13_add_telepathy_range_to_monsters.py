"""add telepathy_range to monsters

Revision ID: 32049986cc13
Revises: cf2e930e7e34
Create Date: 2025-09-02 01:46:39.120204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32049986cc13'
down_revision: Union[str, Sequence[str], None] = 'cf2e930e7e34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Column is optional, so nullable=True
    op.add_column(
        "monsters",
        sa.Column("telepathy_range", sa.Integer(), nullable=True),
    )
    # CHECK: must be NULL or > 0 (short name => ck_monsters_telepathy_range_pos)
    op.create_check_constraint(
        "telepathy_range_pos",
        "monsters",
        "telepathy_range IS NULL OR telepathy_range > 0",
    )
    # Add an index
    op.create_index(
        "ix_monsters_telepathy_range",
        "monsters",
        ["telepathy_range"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_monsters_telepathy_range", table_name="monsters")
    op.drop_constraint("ck_monsters_telepathy_range_pos", "monsters", type_="check")
    op.drop_column("monsters", "telepathy_range")
