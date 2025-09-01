from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin

class MonsterConditionImmunity(Base, ReprMixin):
    """
    One condition immunity per row.
    Enforces uniqueness per monster so the same condition isn't duplicated.
    """
    __tablename__ = "monster_condition_immunities"
    __repr_attrs__ = ("id", "monster_id", "condition")

    __table_args__ = (
        UniqueConstraint("monster_id", "condition", name="uq_condition_per_monster"),
        Index("ix_monster_condition_immunities_condition", "condition"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    monster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    monster = relationship("Monster", back_populates="condition_immunities")

    condition: Mapped[str] = mapped_column(String(32), nullable=False)