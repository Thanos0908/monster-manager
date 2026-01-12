"""SQLAlchemy models for monster damage modifiers (immunities/resistances/vulnerabilities)."""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.enums.monster_enums import DamageType
from backend.utils.mixins import ReprMixin

if TYPE_CHECKING:
    from backend.models.monster import Monster


# Keep DB values as strings, but enforce the allowed set at the DB level.
_DAMAGE_TYPE_VALUES: list[str] = [dt.value for dt in DamageType]
_DAMAGE_TYPES_CHECK = (
    "damage_type IN (" + ",".join(f"'{t}'" for t in _DAMAGE_TYPE_VALUES) + ")"
)


class MonsterDamageImmunity(Base, ReprMixin):
    """
    One damage immunity entry for a monster.
    Each row links a monster to a single damage type (e.g., "Fire") and enforces
    uniqueness so the same type cannot be listed twice per monster.
    """

    __tablename__ = "monster_damage_immunities"
    __repr_attrs__ = ("id", "monster_id", "damage_type")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    monster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("monsters.id", ondelete="CASCADE"), nullable=False,)
    monster: Mapped["Monster"] = relationship("Monster", back_populates="damage_immunities")

    damage_type: Mapped[str] = mapped_column(String(16), nullable=False)

    __table_args__ = (
        UniqueConstraint("monster_id", "damage_type", name="uq_immunity_per_monster_type"),
        CheckConstraint(_DAMAGE_TYPES_CHECK, name="ck_damage_immunity_type"),
        Index("ix_monster_damage_immunities_damage_type", "damage_type"),
    )


class MonsterDamageResistance(Base, ReprMixin):
    """
    One damage resistance entry for a monster.
    Each row links a monster to a single damage type (e.g., "Cold") and enforces
    uniqueness so the same type cannot be listed twice per monster.
    """

    __tablename__ = "monster_damage_resistances"
    __repr_attrs__ = ("id", "monster_id", "damage_type")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    monster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("monsters.id", ondelete="CASCADE"), nullable=False,)
    monster: Mapped["Monster"] = relationship("Monster", back_populates="damage_resistances")

    damage_type: Mapped[str] = mapped_column(String(16), nullable=False)

    __table_args__ = (
        UniqueConstraint("monster_id", "damage_type", name="uq_resistance_per_monster_type"),
        CheckConstraint(_DAMAGE_TYPES_CHECK, name="ck_damage_resistance_type"),
        Index("ix_monster_damage_resistances_damage_type", "damage_type"),
    )


class MonsterDamageVulnerability(Base, ReprMixin):
    """
    One damage vulnerability entry for a monster.
    Each row links a monster to a single damage type (e.g., "Radiant") and enforces
    uniqueness so the same type cannot be listed twice per monster.
    """

    __tablename__ = "monster_damage_vulnerabilities"
    __repr_attrs__ = ("id", "monster_id", "damage_type")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    monster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("monsters.id", ondelete="CASCADE"), nullable=False,)
    monster: Mapped["Monster"] = relationship("Monster", back_populates="damage_vulnerabilities")

    damage_type: Mapped[str] = mapped_column(String(16), nullable=False)

    __table_args__ = (
        UniqueConstraint("monster_id", "damage_type", name="uq_vulnerability_per_monster_type"),
        CheckConstraint(_DAMAGE_TYPES_CHECK, name="ck_damage_vulnerability_type"),
        Index("ix_monster_damage_vulnerabilities_damage_type", "damage_type"),
    )