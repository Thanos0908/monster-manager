from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin

class MonsterMovement(Base, ReprMixin):
    """
    One movement type per row (e.g., walk, fly, swim) with its speed in feet.
    Enforces uniqueness per monster so it avoids duplicate 'movement types' for the same monster.
    """
    __tablename__ = "monster_movement"
    __table_args__ = (
        UniqueConstraint("monster_id", "movement_type", name="uq_movement_per_monster"),
        Index("ix_monster_movement_movement_type", "movement_type"),
        CheckConstraint("speed >= 0", name="speed_nonneg"),
    )

    __repr_attrs__ = ("id", "monster_id", "movement_type", "speed")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    monster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    monster = relationship("Monster", back_populates="movements")

    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)