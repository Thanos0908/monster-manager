"""tidy movement/senses CHECK constraint names

Revision ID: ba3aaca22b22
Revises: 4dd8b91fb3fb
Create Date: 2025-09-01 12:35:06.523639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba3aaca22b22'
down_revision: Union[str, Sequence[str], None] = '4dd8b91fb3fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MonsterMovement
    op.execute(
        "ALTER TABLE monster_movement "
        "RENAME CONSTRAINT ck_monster_movement_ck_monster_movement_speed_nonneg "
        "TO ck_monster_movement_speed_nonneg"
    )
    # MonsterSense (include if you also changed the model to name='range_nonneg')
    op.execute(
        "ALTER TABLE monster_senses "
        "RENAME CONSTRAINT ck_monster_senses_ck_monster_senses_range_nonneg "
        "TO ck_monster_senses_range_nonneg"
    )

def downgrade() -> None:
    # MonsterMovement
    op.execute(
        "ALTER TABLE monster_movement "
        "RENAME CONSTRAINT ck_monster_movement_speed_nonneg "
        "TO ck_monster_movement_ck_monster_movement_speed_nonneg"
    )
    # MonsterSense (mirror if you did the upgrade rename)
    op.execute(
        "ALTER TABLE monster_senses "
        "RENAME CONSTRAINT ck_monster_senses_range_nonneg "
        "TO ck_monster_senses_ck_monster_senses_range_nonneg"
    )