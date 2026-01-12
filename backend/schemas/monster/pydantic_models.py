from __future__ import annotations
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationInfo, computed_field, model_validator
from backend.enums import Alignment, Size
from backend.enums.monster_enums import DamageType, MovementType
from backend.utils.cr_xp import xp_for_cr
from .parts import (
    AbilityScores,
    ConditionItem,
    DamageTagItem,
    LanguageItem,
    MovementItem,
    SavingThrowProficiencies,
    SenseItem,
    SkillProficiencies,
    TraitBlock,
)


class MonsterCreate(BaseModel):
    """
    Payload to create a Monster.

    Matches backend.models.monster.Monster columns + child tables:
    - Strings for size/main_type/subtype/alignment (size/alignment use enums).
    - AC is text ('armor_class_text'); PP/telepathy are integers.
    - HP provided as both number and dice string.
    - Ability scores map 1:1 to model columns (service will decompose).
    - CR uses Decimal; xp_override allowed only for CR 0 (0 or 10).
    - Lists use replace semantics.

    Note:
    - `is_official` is NOT client-settable. Official status is controlled by moderation/admin workflow.
    """
    name: str = Field(min_length=1, max_length=200)
    size: Size
    main_type: str = Field(min_length=1, max_length=64, description="Creature main type, e.g., 'Fiend'.")
    subtype: Optional[str] = Field(default=None, max_length=128)
    alignment: Alignment
    challenge_rating: Decimal = Field(ge=Decimal("0"), le=Decimal("30"))
    xp_override: Optional[int] = Field(
        default=None,
        description="Only valid for CR 0: must be 0 or 10. Otherwise must be null.",
    )
    armor_class_text: str = Field(min_length=1, max_length=200, description="e.g., '16 (natural armor)'.")
    passive_perception: int = Field(ge=0)
    telepathy_range: Optional[int] = Field(default=None, ge=0)
    hit_points: int = Field(ge=1, le=2000)
    hit_points_dice: str = Field(pattern=r"^\d+d\d+(?:[+-]\d+)?$", max_length=50)
    ability_scores: AbilityScores
    saving_throws: Optional[SavingThrowProficiencies] = None
    skills: Optional[SkillProficiencies] = None
    movement: List[MovementItem] = Field(default_factory=list)
    senses: List[SenseItem] = Field(default_factory=list)
    languages: List[LanguageItem] = Field(default_factory=list)
    damage_immunities: List[DamageTagItem] = Field(default_factory=list)
    damage_resistances: List[DamageTagItem] = Field(default_factory=list)
    damage_vulnerabilities: List[DamageTagItem] = Field(default_factory=list)
    condition_immunities: List[ConditionItem] = Field(default_factory=list)
    traits: List[TraitBlock] = Field(default_factory=list)
    actions: List[TraitBlock] = Field(default_factory=list)
    reactions: List[TraitBlock] = Field(default_factory=list)
    legendary_actions: List[TraitBlock] = Field(default_factory=list)
    lair_actions: List[str] = Field(default_factory=list, description="Freeform bullet strings.")
    regional_effects: List[str] = Field(default_factory=list, description="Freeform bullet strings.")
    backstory: Optional[str] = Field(default=None, max_length=10_000)

    @model_validator(mode="after")
    def _validate_xp_override_vs_cr(self):
        # CR 0: xp_override ∈ {None, 0, 10}; else must be None
        if self.challenge_rating == Decimal("0"):
            if self.xp_override not in (None, 0, 10):
                raise ValueError("When challenge_rating is 0, xp_override must be 0 or 10.")
        else:
            if self.xp_override is not None:
                raise ValueError("When challenge_rating is not 0, xp_override must be null.")
        return self

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
        "validate_default": True,
    }


class MonsterUpdate(BaseModel):
    """
    PATCH-style update for a Monster.
    Rules (recap):
    - All fields optional; omitted ⇒ keep existing value.
    - Required scalars: if explicitly null ⇒ keep existing value (ignore).
    - Collections (lists): omitted ⇒ keep; [] ⇒ clear; null ⇒ keep.
    - Optional scalars (like backstory/subtype/telepathy_range): null ⇒ clear.
    - Name is immutable (not included here).
    - Any save by a DM sets is_official=False server-side.
    - Any save by an admin sets is_official=True server-side.
    - CR 0 rule: xp_override allowed only at CR 0 and must be 0 or 10.
    - Transition 0 → non-0: if payload includes numeric xp_override ⇒ error.
      (Omitted/null xp_override is okay; service will ensure DB value ends up None.)
    - Movement: hover=True requires a 'fly' movement in the provided list.
    - Damage types cannot appear in more than one of {immunities, resistances, vulnerabilities}.
    """
    size: Optional[Size] = None
    main_type: Optional[str] = Field(default=None, max_length=64)
    subtype: Optional[str] = Field(default=None, max_length=128)
    alignment: Optional[Alignment] = None
    challenge_rating: Optional[Decimal] = Field(default=None, ge=Decimal("0"), le=Decimal("30"))
    xp_override: Optional[int] = Field(
        default=None,
        description="Only valid when CR is (or remains) 0: 0 or 10. Null/omitted means 'keep existing'.",
    )
    armor_class_text: Optional[str] = Field(default=None, max_length=200)
    passive_perception: Optional[int] = Field(default=None, ge=0)
    telepathy_range: Optional[int] = Field(default=None, ge=0)
    hit_points: Optional[int] = Field(default=None, ge=1, le=2000)
    hit_points_dice: Optional[str] = Field(default=None, max_length=50, pattern=r"^\d+d\d+(?:[+-]\d+)?$")
    ability_scores: Optional[AbilityScores] = None
    saving_throws: Optional[SavingThrowProficiencies] = None
    skills: Optional[SkillProficiencies] = None
    movement: Optional[List[MovementItem]] = Field(default=None)
    senses: Optional[List[SenseItem]] = Field(default=None)
    languages: Optional[List[LanguageItem]] = Field(default=None)
    damage_immunities: Optional[List[DamageTagItem]] = Field(default=None)
    damage_resistances: Optional[List[DamageTagItem]] = Field(default=None)
    damage_vulnerabilities: Optional[List[DamageTagItem]] = Field(default=None)
    condition_immunities: Optional[List[ConditionItem]] = Field(default=None)
    traits: Optional[List[TraitBlock]] = Field(default=None)
    actions: Optional[List[TraitBlock]] = Field(default=None)
    reactions: Optional[List[TraitBlock]] = Field(default=None)
    legendary_actions: Optional[List[TraitBlock]] = Field(default=None)
    lair_actions: Optional[List[str]] = Field(default=None)
    regional_effects: Optional[List[str]] = Field(default=None)
    backstory: Optional[str] = Field(default=None, max_length=10_000)

    @model_validator(mode="after")
    def _validate_cr_xp_rules(self, info: ValidationInfo):
        """
        Enforce CR/xp_override constraints with context support:
        Pass current DB CR as `context={"current_cr": Decimal(...)}`.
        """
        current_cr: Optional[Decimal] = None
        if info.context and "current_cr" in info.context:
            current_cr = info.context["current_cr"]

        effective_cr = self.challenge_rating if self.challenge_rating is not None else current_cr

        if effective_cr is not None:
            if effective_cr == Decimal("0"):
                if self.xp_override not in (None, 0, 10):
                    raise ValueError(
                        "When challenge_rating is 0, xp_override must be 0 or 10 (or omitted/null to keep)."
                    )
            else:
                if isinstance(self.xp_override, int):
                    raise ValueError("When challenge_rating is not 0, xp_override must be omitted or null.")
        else:
            if isinstance(self.xp_override, int) and current_cr != Decimal("0"):
                raise ValueError("xp_override numeric is only valid when current CR is 0.")
        return self

    @model_validator(mode="after")
    def _validate_movement_hover(self):
        if self.movement is not None:
            has_fly = any(m.type == MovementType.FLY for m in self.movement)
            has_hover = any(m.hover for m in self.movement)
            if has_hover and not has_fly:
                raise ValueError("Movement 'hover' can only be true if a 'fly' movement is present.")
        return self

    @model_validator(mode="after")
    def _validate_damage_buckets(self):
        if any(v is not None for v in (self.damage_immunities, self.damage_resistances, self.damage_vulnerabilities)):
            imm: set[DamageType] = {x.type for x in (self.damage_immunities or [])}
            res: set[DamageType] = {x.type for x in (self.damage_resistances or [])}
            vul: set[DamageType] = {x.type for x in (self.damage_vulnerabilities or [])}

            if (imm & res) or (imm & vul) or (res & vul):
                raise ValueError(
                    "A damage type cannot be in more than one of {immunities, resistances, vulnerabilities}."
                )
        return self

    def to_update_dict(self, *, current_cr: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Convert the validated PATCH payload to a dict of DB updates, applying our omit/clear rules:
        - Required scalars: None ⇒ omit (keep)
        - Collections: None ⇒ omit; [] ⇒ clear; list ⇒ replace
        - Optional scalars (subtype, telepathy_range, backstory): include even if None (clear)
        - CR/XP: enforce normalization (xp_override omitted unless valid to set at CR 0)

        Pass current_cr if you didn't pass context during validation.
        """
        data = self.model_dump(mode="python")

        required_scalars = {
            "size", "main_type", "alignment",
            "armor_class_text", "passive_perception",
            "hit_points", "hit_points_dice",
            "ability_scores",
        }
        list_fields = {
            "movement", "senses", "languages",
            "damage_immunities", "damage_resistances", "damage_vulnerabilities",
            "condition_immunities",
            "traits", "actions", "reactions", "legendary_actions",
            "lair_actions", "regional_effects",
            "saving_throws", "skills",
        }
        optional_clearables = {"subtype", "telepathy_range", "backstory"}

        update: Dict[str, Any] = {}

        for field in required_scalars:
            if field in data and data[field] is not None:
                update[field] = data[field]

        for field in list_fields:
            if field in data:
                val = data[field]
                if val is None:
                    continue
                update[field] = val

        for field in optional_clearables:
            if field in data:
                update[field] = data[field]

        if "challenge_rating" in data and data["challenge_rating"] is not None:
            update["challenge_rating"] = data["challenge_rating"]

        eff_cr = update.get("challenge_rating", current_cr)
        if "xp_override" in data:
            xo = data["xp_override"]
            if eff_cr == Decimal("0"):
                if xo in (0, 10):
                    update["xp_override"] = xo
        return update

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
        "validate_default": True,
    }


class MonsterRead(BaseModel):
    """
    Public read model. Routes/services enforce monster visibility rules
    (e.g., DM/Player see official-only; Admin may see all).
    """
    id: int
    name: str
    size: Size
    main_type: str
    subtype: Optional[str] = None
    alignment: Alignment
    challenge_rating: Decimal
    xp_override: Optional[int] = None  # echoed for transparency; null unless CR==0
    armor_class_text: str
    passive_perception: int
    telepathy_range: Optional[int] = None
    hit_points: int
    hit_points_dice: str
    ability_scores: AbilityScores
    saving_throws: Optional[SavingThrowProficiencies] = None
    skills: Optional[SkillProficiencies] = None
    movement: List[MovementItem] = Field(default_factory=list)
    senses: List[SenseItem] = Field(default_factory=list)
    languages: List[LanguageItem] = Field(default_factory=list)
    damage_immunities: List[DamageTagItem] = Field(default_factory=list)
    damage_resistances: List[DamageTagItem] = Field(default_factory=list)
    damage_vulnerabilities: List[DamageTagItem] = Field(default_factory=list)
    condition_immunities: List[ConditionItem] = Field(default_factory=list)
    traits: List[TraitBlock] = Field(default_factory=list)
    actions: List[TraitBlock] = Field(default_factory=list)
    reactions: List[TraitBlock] = Field(default_factory=list)
    legendary_actions: List[TraitBlock] = Field(default_factory=list)
    lair_actions: List[str] = Field(default_factory=list)
    regional_effects: List[str] = Field(default_factory=list)
    backstory: Optional[str] = None

    @computed_field
    @property
    def xp(self) -> int:
        """Display XP: use override for CR 0 when present, else CR→XP map."""
        if self.challenge_rating == Decimal("0") and self.xp_override in (0, 10):
            return int(self.xp_override)
        return xp_for_cr(self.challenge_rating)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class MonsterReadAdmin(MonsterRead):
    """Admin read model. Same as public, but includes `is_official`."""
    is_official: bool


class MonsterListItem(BaseModel):
    """
    Lightweight row model for lists/search/autocomplete.
    Visibility is handled by route/service filters.
    """
    id: int
    name: str
    size: Size
    main_type: str
    subtype: Optional[str] = None
    challenge_rating: Decimal
    xp_override: Optional[int] = None  # only used when CR == 0

    @computed_field  # type: ignore[misc]
    @property
    def xp(self) -> int:
        if self.challenge_rating == Decimal("0") and self.xp_override in (0, 10):
            return int(self.xp_override)
        return xp_for_cr(self.challenge_rating)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


__all__ = [
    "MonsterCreate",
    "MonsterUpdate",
    "MonsterRead",
    "MonsterReadAdmin",
    "MonsterListItem",
]