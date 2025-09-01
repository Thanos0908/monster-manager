from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin

class MonsterLanguage(Base, ReprMixin):
    """
    One language per row. Unique per monster.
    """
    __tablename__ = "monster_languages"
    __table_args__ = (
        UniqueConstraint("monster_id", "language", name="uq_language_per_monster"),
        Index("ix_monster_languages_language", "language"),
    )

    __repr_attrs__ = ("id", "monster_id", "language")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    monster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monsters.id", ondelete="CASCADE"),
        nullable=False,                      
    )
    monster = relationship("Monster", back_populates="languages")

    language: Mapped[str] = mapped_column(String(64), nullable=False)