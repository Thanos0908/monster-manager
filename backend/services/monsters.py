"""backend.services.monsters
Monster domain write operations.
Used by:
    - POST /monsters/new (SSR)
    - POST /monsters/{id}/edit (admin SSR)
    - POST /monsters/{id}/delete (admin SSR)
Rules enforced here:
    - Role gating: only ADMIN or DM can create.
    - DM submissions are always non-official and owned by the DM.
    - Admin creations are official (owner_id = NULL).
    - Case-insensitive unique name (maps DB constraint to a friendly error).
"""
from __future__ import annotations
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.monster import Monster
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
from backend.schemas.monster.pydantic_models import MonsterCreate
from uuid import UUID


class MonsterCreateError(Exception):
    """Base class for monster creation errors."""


class MonsterNameAlreadyExistsError(MonsterCreateError):
    """Raised when a monster with the same (case-insensitive) name already exists."""


def _role_value(user: User) -> str:
    return str(getattr(user.role, "value", user.role)).lower()


async def create_monster(*, actor: User, payload: MonsterCreate, session: AsyncSession) -> Monster:
    """Create and persist a Monster and its child rows."""
    role = _role_value(actor)
    if role not in {"admin", "dm"}:
        raise MonsterCreateError("Only admins and DMs can create monsters")

    is_admin = role == "admin"

    monster = Monster(
        owner_id=None if is_admin else actor.id,
        name=payload.name,
        challenge_rating=payload.challenge_rating,
        xp_override=payload.xp_override,
        armor_class_text=payload.armor_class_text,
        passive_perception=payload.passive_perception,
        telepathy_range=payload.telepathy_range,
        size=payload.size.value,
        main_type=payload.main_type,
        subtype=payload.subtype,
        alignment=payload.alignment.value,
        hit_points=payload.hit_points,
        hit_points_dice=payload.hit_points_dice,
        str_score=payload.ability_scores.STR,
        dex_score=payload.ability_scores.DEX,
        con_score=payload.ability_scores.CON,
        int_score=payload.ability_scores.INT,
        wis_score=payload.ability_scores.WIS,
        cha_score=payload.ability_scores.CHA,
        saving_throw_proficiencies=(payload.saving_throws.model_dump() if payload.saving_throws else None),
        skill_proficiencies=(payload.skills.model_dump() if payload.skills else None),
        traits=[t.model_dump() for t in payload.traits] or None,
        actions=[a.model_dump() for a in payload.actions] or None,
        reactions=[r.model_dump() for r in payload.reactions] or None,
        legendary_actions=[l.model_dump() for l in payload.legendary_actions] or None,
        lair_actions=payload.lair_actions or None,
        regional_effects=payload.regional_effects or None,
        backstory=payload.backstory,
        is_official=is_admin,
    )

    session.add(monster)

    try:
        await session.flush()  # ensures monster.id exists

        # Child rows
        for m in payload.movement:
            session.add(MonsterMovement(monster_id=monster.id, movement_type=m.type.value, speed=m.speed, hover=m.hover,))

        for s in payload.senses:
            session.add(MonsterSense(monster_id=monster.id, sense=s.sense.value, range=s.range))

        for lang in payload.languages:
            session.add(MonsterLanguage(monster_id=monster.id, language=lang.LanguageItem.value))

        for dmg in payload.damage_immunities:
            session.add(MonsterDamageImmunity(monster_id=monster.id, damage_type=dmg.type.value))

        for dmg in payload.damage_resistances:
            session.add(MonsterDamageResistance(monster_id=monster.id, damage_type=dmg.type.value))

        for dmg in payload.damage_vulnerabilities:
            session.add(MonsterDamageVulnerability(monster_id=monster.id, damage_type=dmg.type.value))

        for c in payload.condition_immunities:
            session.add(MonsterConditionImmunity(monster_id=monster.id, condition=c.condition.value))

        await session.commit()
        return monster

    except IntegrityError as exc:
        await session.rollback()

        # Friendly mapping for the case-insensitive unique name constraint.
        msg = str(getattr(exc, "orig", exc)).lower()
        if "uq_monsters_lower_name" in msg:
            raise MonsterNameAlreadyExistsError() from exc

        raise


class MonsterNotFoundError(Exception):
    """Raised when the monster does not exist."""
   
    
async def delete_monster_admin(*, monster_id: UUID, session: AsyncSession) -> None:
    """
    Admin-only delete.
    Deletes the monster row; child rows should be removed by FK cascades or ORM cascade rules.
    """
    monster = await session.get(Monster, monster_id)
    if monster is None:
        raise MonsterNotFoundError()

    await session.delete(monster)
    await session.commit()


async def update_monster_full_replace_admin(
    *,
    monster: Monster,
    payload: MonsterCreate,
    session: AsyncSession,
) -> Monster:
    """
    Admin-only full replace update.
    - Overwrites scalar + JSON fields
    - Deletes & recreates child rows
    - Sets is_official=True (admin write)
    - Sets owner_id=None (treat as official/admin-maintained)
    """
    # Scalars / JSON
    monster.owner_id = None
    monster.is_official = True
    monster.name = payload.name
    monster.challenge_rating = payload.challenge_rating
    monster.xp_override = payload.xp_override
    monster.armor_class_text = payload.armor_class_text
    monster.passive_perception = payload.passive_perception
    monster.telepathy_range = payload.telepathy_range
    monster.size = payload.size.value
    monster.main_type = payload.main_type
    monster.subtype = payload.subtype
    monster.alignment = payload.alignment.value
    monster.hit_points = payload.hit_points
    monster.hit_points_dice = payload.hit_points_dice
    monster.str_score = payload.ability_scores.STR
    monster.dex_score = payload.ability_scores.DEX
    monster.con_score = payload.ability_scores.CON
    monster.int_score = payload.ability_scores.INT
    monster.wis_score = payload.ability_scores.WIS
    monster.cha_score = payload.ability_scores.CHA
    monster.saving_throw_proficiencies = payload.saving_throws.model_dump() if payload.saving_throws else None
    monster.skill_proficiencies = payload.skills.model_dump() if payload.skills else None
    monster.traits = [t.model_dump() for t in payload.traits] or None
    monster.actions = [a.model_dump() for a in payload.actions] or None
    monster.reactions = [r.model_dump() for r in payload.reactions] or None
    monster.legendary_actions = [l.model_dump() for l in payload.legendary_actions] or None
    monster.lair_actions = payload.lair_actions or None
    monster.regional_effects = payload.regional_effects or None
    monster.backstory = payload.backstory

    try:
        # Clear child tables (replace semantics)
        await session.execute(delete(MonsterMovement).where(MonsterMovement.monster_id == monster.id))
        await session.execute(delete(MonsterSense).where(MonsterSense.monster_id == monster.id))
        await session.execute(delete(MonsterLanguage).where(MonsterLanguage.monster_id == monster.id))
        await session.execute(delete(MonsterDamageImmunity).where(MonsterDamageImmunity.monster_id == monster.id))
        await session.execute(delete(MonsterDamageResistance).where(MonsterDamageResistance.monster_id == monster.id))
        await session.execute(delete(MonsterDamageVulnerability).where(MonsterDamageVulnerability.monster_id == monster.id))
        await session.execute(delete(MonsterConditionImmunity).where(MonsterConditionImmunity.monster_id == monster.id))

        await session.flush()

        # Recreate child rows
        for m in payload.movement:
            session.add(MonsterMovement(monster_id=monster.id, movement_type=m.type.value, speed=m.speed, hover=m.hover))
        for s in payload.senses:
            session.add(MonsterSense(monster_id=monster.id, sense=s.sense.value, range=s.range))
        for lang in payload.languages:
            session.add(MonsterLanguage(monster_id=monster.id, language=lang.LanguageItem.value))
        for dmg in payload.damage_immunities:
            session.add(MonsterDamageImmunity(monster_id=monster.id, damage_type=dmg.type.value))
        for dmg in payload.damage_resistances:
            session.add(MonsterDamageResistance(monster_id=monster.id, damage_type=dmg.type.value))
        for dmg in payload.damage_vulnerabilities:
            session.add(MonsterDamageVulnerability(monster_id=monster.id, damage_type=dmg.type.value))
        for c in payload.condition_immunities:
            session.add(MonsterConditionImmunity(monster_id=monster.id, condition=c.condition.value))

        await session.commit()
        return monster

    except IntegrityError as exc:
        await session.rollback()

        msg = str(getattr(exc, "orig", exc)).lower()
        if "uq_monsters_lower_name" in msg:
            raise MonsterNameAlreadyExistsError() from exc

        raise