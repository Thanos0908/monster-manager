from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base

class MonsterLanguage(Base):
    """
    One language per row
    Enforces uniqueness per monster so the same language isn't duplicated.
    """
    __tablename__ = "monster_languages"
    __table_args__ = (
        UniqueConstraint("monster_id", "language", name="uq_language_per_monster"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    monster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monsters.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    monster = relationship("Monster", back_populates="languages")

    language: Mapped[str] = mapped_column(String(64), nullable=False)