"""add challenge_rating to monsters

Revision ID: 367e50c499d6
Revises: ba3aaca22b22
Create Date: 2025-09-02 00:37:49.778807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '367e50c499d6'
down_revision: Union[str, Sequence[str], None] = 'ba3aaca22b22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add column (nullable first so we can backfill safely)
    op.add_column(
        "monsters",
        sa.Column("challenge_rating", sa.Numeric(5, 3), nullable=True),
    )

    # 2) Backfill existing rows to a valid CR (0)
    op.execute("UPDATE monsters SET challenge_rating = 0 WHERE challenge_rating IS NULL")

    # 3) Enforce NOT NULL
    op.alter_column("monsters", "challenge_rating", nullable=False)

    # 4) Add index (guard with IF NOT EXISTS to avoid dup if autogen also creates it)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_monsters_challenge_rating ON monsters (challenge_rating)"
    )

    # 5) Restrict to official 5e CR values
    op.create_check_constraint(
        "ck_monsters_challenge_rating_allowed",
        "monsters",
        """
        challenge_rating IN (
            0,
            0.125, 0.25, 0.5,
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
            11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
            21, 22, 23, 24, 25, 26, 27, 28, 29, 30
        )
        """,
    )


def downgrade() -> None:
    # Drop CHECK, index, and column
    op.drop_constraint("ck_monsters_challenge_rating_allowed", "monsters", type_="check")
    op.execute("DROP INDEX IF EXISTS ix_monsters_challenge_rating")
    op.drop_column("monsters", "challenge_rating")
