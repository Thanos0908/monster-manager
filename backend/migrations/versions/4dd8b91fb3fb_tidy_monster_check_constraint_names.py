"""tidy monster CHECK constraint names

Revision ID: 4dd8b91fb3fb
Revises: 3a69354719ac
Create Date: 2025-09-01 12:15:17.360681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "4dd8b91fb3fb"
down_revision: Union[str, Sequence[str], None] = "3a69354719ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename double-prefixed monster CHECK constraints to tidy names that align with naming_convention
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_ck_monsters_hit_points_positive TO ck_monsters_hit_points_positive"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_ck_monsters_str_1_30 TO ck_monsters_str_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_ck_monsters_dex_1_30 TO ck_monsters_dex_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_ck_monsters_con_1_30 TO ck_monsters_con_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_ck_monsters_int_1_30 TO ck_monsters_int_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_ck_monsters_wis_1_30 TO ck_monsters_wis_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_ck_monsters_cha_1_30 TO ck_monsters_cha_1_30"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert monster CHECK constraint names to the previous double-prefixed form
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_hit_points_positive TO ck_monsters_ck_monsters_hit_points_positive"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_str_1_30 TO ck_monsters_ck_monsters_str_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_dex_1_30 TO ck_monsters_ck_monsters_dex_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_con_1_30 TO ck_monsters_ck_monsters_con_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_int_1_30 TO ck_monsters_ck_monsters_int_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_wis_1_30 TO ck_monsters_ck_monsters_wis_1_30"
    )
    op.execute(
        "ALTER TABLE monsters RENAME CONSTRAINT ck_monsters_cha_1_30 TO ck_monsters_ck_monsters_cha_1_30"
    )