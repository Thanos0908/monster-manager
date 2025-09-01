"""add armor_class_text to monsters

Revision ID: 74b089e298b9
Revises: e63cef2622d2
Create Date: 2025-09-02 00:58:46.412670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74b089e298b9'
down_revision: Union[str, Sequence[str], None] = 'e63cef2622d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # table is empty, so we can add NOT NULL directly
    op.add_column(
        "monsters",
        sa.Column("armor_class_text", sa.String(length=200), nullable=False),
    )
    # use short name so naming_convention yields ck_monsters_armor_class_nonblank
    op.create_check_constraint(
        "armor_class_nonblank",
        "monsters",
        "btrim(armor_class_text) <> ''",
    )

def downgrade() -> None:
    op.drop_constraint("ck_monsters_armor_class_nonblank", "monsters", type_="check")
    op.drop_column("monsters", "armor_class_text")
