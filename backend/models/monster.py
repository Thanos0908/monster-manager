"""SQLAlchemy model for the core Monster entity and its persisted fields."""

from __future__ import annotations
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin, StrMixin

if TYPE_CHECKING:
    from backend.models.monster_condition_immunity import MonsterConditionImmunity
    from backend.models.monster_damage import (
        MonsterDamageImmunity,
        MonsterDamageResistance,
        MonsterDamageVulnerability,
    )
    from backend.models.monster_languages import MonsterLanguage
    from backend.models.monster_movement import MonsterMovement
    from backend.models.monster_senses import MonsterSense
    from backend.models.user import User


class Monster(Base, ReprMixin, StrMixin):
    """
    Core monster entity.

    Moderation workflow:
    - New monsters start as is_official=False.
    - Non-official monsters are intended to be visible only to admins
      (enforced in authorization filter + dependencies).
    """

    __tablename__ = "monsters"
    __repr_attrs__ = ("id", "owner_id", "name")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Keep monsters even if the creating user is deleted.
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    owner: Mapped[Optional["User"]] = relationship(
        "User", back_populates="monsters", lazy="selectin"
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    challenge_rating: Mapped[Decimal] = mapped_column(
        Numeric(5, 3),
        nullable=False,
        index=True,
    )
    xp_override: Mapped[int | None] = mapped_column(Integer, nullable=True)

    armor_class_text: Mapped[str] = mapped_column(String(200), nullable=False)
    passive_perception: Mapped[int] = mapped_column(Integer, nullable=False)
    telepathy_range: Mapped[int | None] = mapped_column(Integer, nullable=True)

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

    saving_throw_proficiencies: Mapped[dict[str, int] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )
    skill_proficiencies: Mapped[dict[str, int] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )

    traits: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )
    actions: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )
    reactions: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )
    bonus_actions: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )
    legendary_actions: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )
    lair_actions: Mapped[list[str] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )
    regional_effects: Mapped[list[str] | None] = mapped_column(
        JSONB(astext_type=Text()),
        nullable=True,
    )

    movements: Mapped[list["MonsterMovement"]] = relationship(
        back_populates="monster",
        cascade="all, delete-orphan",
    )
    senses: Mapped[list["MonsterSense"]] = relationship(
        back_populates="monster",
        cascade="all, delete-orphan",
    )
    languages: Mapped[list["MonsterLanguage"]] = relationship(
        back_populates="monster",
        cascade="all, delete-orphan",
    )
    condition_immunities: Mapped[list["MonsterConditionImmunity"]] = relationship(
        back_populates="monster",
        cascade="all, delete-orphan",
    )
    damage_immunities: Mapped[list["MonsterDamageImmunity"]] = relationship(
        back_populates="monster",
        cascade="all, delete-orphan",
    )
    damage_resistances: Mapped[list["MonsterDamageResistance"]] = relationship(
        back_populates="monster",
        cascade="all, delete-orphan",
    )
    damage_vulnerabilities: Mapped[list["MonsterDamageVulnerability"]] = relationship(
        back_populates="monster",
        cascade="all, delete-orphan",
    )

    backstory: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_official: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    __table_args__ = (
        # Global, case-insensitive uniqueness on name
        Index("uq_monsters_lower_name", func.lower(name), unique=True),
        # Data validation
        CheckConstraint("hit_points > 0", name="hit_points_positive"),
        CheckConstraint("str_score BETWEEN 1 AND 30", name="str_1_30"),
        CheckConstraint("dex_score BETWEEN 1 AND 30", name="dex_1_30"),
        CheckConstraint("con_score BETWEEN 1 AND 30", name="con_1_30"),
        CheckConstraint("int_score BETWEEN 1 AND 30", name="int_1_30"),
        CheckConstraint("wis_score BETWEEN 1 AND 30", name="wis_1_30"),
        CheckConstraint("cha_score BETWEEN 1 AND 30", name="cha_1_30"),
        CheckConstraint(
            """
            challenge_rating IN (
                0,
                0.125, 0.25, 0.5,
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                21, 22, 23, 24, 25, 26, 27, 28, 29, 30
            )
            """,
            name="challenge_rating_allowed",
        ),
        CheckConstraint("btrim(armor_class_text) <> ''", name="armor_class_nonblank"),
        CheckConstraint("passive_perception >= 0", name="passive_perception_nonneg"),
        CheckConstraint("telepathy_range > 0", name="telepathy_range_pos"),
        CheckConstraint(
            """
            (challenge_rating = 0 AND (xp_override IN (0, 10) OR xp_override IS NULL))
            OR (challenge_rating <> 0 AND xp_override IS NULL)
            """,
            name="xp_override_valid",
        ),
    )