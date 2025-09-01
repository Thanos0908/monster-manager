"""add passive_perception to monsters

Revision ID: cf2e930e7e34
Revises: 74b089e298b9
Create Date: 2025-09-02 01:22:45.789377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf2e930e7e34'
down_revision: Union[str, Sequence[str], None] = '74b089e298b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # table is empty, so we can add NOT NULL directly
    op.add_column(
        "monsters",
        sa.Column("passive_perception", sa.Integer(), nullable=False),
    )
    # short name so naming_convention yields ck_monsters_passive_perception_nonneg
    op.create_check_constraint(
        "passive_perception_nonneg",
        "monsters",
        "passive_perception >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_monsters_passive_perception_nonneg", "monsters", type_="check")
    op.drop_column("monsters", "passive_perception")
