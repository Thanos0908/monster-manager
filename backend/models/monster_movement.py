from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base


class MonsterMovement(Base):
    """
    One movement type per row (e.g., walk, fly, swim) with its speed in feet.
    Enforces uniqueness per monster so it avoids duplicate 'movement types' for the same monster.
    """
    __tablename__ = "monster_movement"
    __table_args__ = (
        UniqueConstraint("monster_id", "movement_type", name="uq_movement_per_monster"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    monster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monsters.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    
    monster = relationship("Monster", back_populates="movements")

    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)  
    speed: Mapped[int] = mapped_column(Integer, nullable=False)