"""add monster_condition_immunities table

Revision ID: ac1c9a210abd
Revises: 32049986cc13
Create Date: 2025-09-02 02:07:27.536384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql


# revision identifiers, used by Alembic.
revision: str = 'ac1c9a210abd'
down_revision: Union[str, Sequence[str], None] = '32049986cc13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monster_condition_immunities",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("monster_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("condition", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["monster_id"], ["monsters.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("monster_id", "condition", name="uq_condition_per_monster"),
    )
    op.create_index(
        "ix_monster_condition_immunities_condition",
        "monster_condition_immunities",
        ["condition"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_monster_condition_immunities_condition",
        table_name="monster_condition_immunities",
    )
    op.drop_table("monster_condition_immunities")
