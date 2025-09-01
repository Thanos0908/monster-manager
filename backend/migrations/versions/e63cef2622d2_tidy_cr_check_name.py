"""tidy CR check name

Revision ID: e63cef2622d2
Revises: 367e50c499d6
Create Date: 2025-09-02 00:44:50.806984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e63cef2622d2'
down_revision: Union[str, Sequence[str], None] = '367e50c499d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE monsters "
        "RENAME CONSTRAINT ck_monsters_ck_monsters_challenge_rating_allowed "
        "TO ck_monsters_challenge_rating_allowed"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE monsters "
        "RENAME CONSTRAINT ck_monsters_challenge_rating_allowed "
        "TO ck_monsters_ck_monsters_challenge_rating_allowed"
    )
