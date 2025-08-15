from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin, StrMixin
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.models.monster_movement import MonsterMovement
    from backend.models.monster_senses import MonsterSense
    from backend.models.monster_languages import MonsterLanguage


class Monster(Base, ReprMixin, StrMixin):
    __tablename__ = "monsters"
    __repr_attrs__ = ("id", "owner_id", "name")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    owner = relationship("User", back_populates="monsters", lazy="joined")

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Case-insensitive uniqueness on name 
    __table_args__ = (
        Index("uq_monsters_lower_name", func.lower(name), unique=True),
    )
    
    size: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    main_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  
    subtype: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)      
    alignment: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    hit_points: Mapped[int] = mapped_column(Integer, nullable=False)
    hit_points_dice: Mapped[str] = mapped_column(String(50), nullable=False)

    str_score: Mapped[int] = mapped_column(Integer, nullable=False)
    dex_score: Mapped[int] = mapped_column(Integer, nullable=False)
    con_score: Mapped[int] = mapped_column(Integer, nullable=False)
    int_score: Mapped[int] = mapped_column(Integer, nullable=False)
    wis_score: Mapped[int] = mapped_column(Integer, nullable=False)
    cha_score: Mapped[int] = mapped_column(Integer, nullable=False)

    movements: Mapped[list["MonsterMovement"]] = relationship(back_populates="monster", cascade="all, delete-orphan")
    senses: Mapped[list["MonsterSense"]] = relationship(back_populates="monster", cascade="all, delete-orphan")
    languages: Mapped[list["MonsterLanguage"]] = relationship(back_populates="monster", cascade="all, delete-orphan")           

    backstory: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)