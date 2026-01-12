"""These are reusable monster schema components used by MonsterCreate/MonsterUpdate/MonsterRead, 
and enums validate allowed keys."""

from __future__ import annotations
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator
from backend.enums.monster_enums import (
    Ability,
    Skill,
    DamageType,
    Condition,
    Sense,
    MovementType,
    Language,
)


class AbilityScores(BaseModel):
    """Six core ability scores (1..30)."""
    STR: int = Field(ge=1, le=30)
    DEX: int = Field(ge=1, le=30)
    CON: int = Field(ge=1, le=30)
    INT: int = Field(ge=1, le=30)
    WIS: int = Field(ge=1, le=30)
    CHA: int = Field(ge=1, le=30)

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class SavingThrowProficiencies(BaseModel):
    """
    Map of ability -> bonus (0..19).

    JSON shape example:
      { "bonuses": { "CON": 14, "WIS": 6 } }

    Keys must match the Ability enum values (STR/DEX/CON/INT/WIS/CHA).
    """
    bonuses: Dict[Ability, int] = Field(default_factory=dict)

    @field_validator("bonuses")
    @classmethod
    def _validate_bonuses(cls, v: Dict[Ability, int]) -> Dict[Ability, int]:
        for ab, bonus in v.items():
            if not (0 <= bonus <= 19):
                raise ValueError(f"Saving throw bonus for {ab} must be between 0 and 19.")
        return v

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class SkillProficiencies(BaseModel):
    """
    Map of skill -> bonus (0..19).

    JSON shape example:
      { "bonuses": { "Perception": 10, "Stealth": 8 } }

    Keys must match the Skill enum values.
    """
    bonuses: Dict[Skill, int] = Field(default_factory=dict)

    @field_validator("bonuses")
    @classmethod
    def _validate_bonuses(cls, v: Dict[Skill, int]) -> Dict[Skill, int]:
        for sk, bonus in v.items():
            if not (0 <= bonus <= 19):
                raise ValueError(f"Skill bonus for {sk} must be between 0 and 19.")
        return v

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class TraitBlock(BaseModel):
    """Reusable Name/Text block for traits, actions, reactions, legendary, bonus actions."""
    name: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class MovementItem(BaseModel):
    """
    One movement mode per type.
    - speed: feet per round (>0)
    - hover: only valid when type == fly
    """
    type: MovementType
    speed: int = Field(ge=1)
    hover: bool = False

    @field_validator("hover")
    @classmethod
    def _hover_only_for_fly(cls, v: bool, info):
        # If hover=True, movement type must be fly (missing type is invalid too).
        if not v:
            return v

        data = info.data  # contains already-validated fields
        mtype: Optional[MovementType] = data.get("type")
        if mtype != MovementType.FLY:
            raise ValueError("hover can only be True when movement type is 'fly'.")
        return v

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class SenseItem(BaseModel):
    """One sense per type (range in feet, >0)."""
    sense: Sense
    range: int = Field(ge=1)

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class LanguageItem(BaseModel):
    """One language tag."""
    LanguageItem: Language

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class DamageTagItem(BaseModel):
    """For immunities/resistances/vulnerabilities: one damage type per row."""
    type: DamageType

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class ConditionItem(BaseModel):
    """For condition immunities: one condition per row."""
    condition: Condition

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


__all__ = [
    "AbilityScores",
    "SavingThrowProficiencies",
    "SkillProficiencies",
    "TraitBlock",
    "MovementItem",
    "SenseItem",
    "LanguageItem",
    "DamageTagItem",
    "ConditionItem",
]