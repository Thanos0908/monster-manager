from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin

class MonsterSense(Base, ReprMixin):
    """
    One sense per row with range in feet.
    Enforces uniqueness per monster to avoid duplication on the same sense.
    """
    __tablename__ = "monster_senses"
    __table_args__ = (
        UniqueConstraint("monster_id", "sense", name="uq_sense_per_monster"),
        Index("ix_monster_senses_sense", "sense"),
        CheckConstraint("range >= 0", name="range_nonneg")
    )

    __repr_attrs__ = ("id", "monster_id", "sense", "range")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    monster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    monster = relationship("Monster", back_populates="senses")

    sense: Mapped[str] = mapped_column(String(32), nullable=False)
    range: Mapped[int] = mapped_column(Integer, nullable=False)  