from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import admin_only
from backend.core.database import get_session
from backend.enums.monster_enums import (
    Ability,
    Alignment,
    Condition,
    DamageType,
    Language,
    MovementType,
    Sense,
    Size,
    Skill,
)
from backend.forms.monsters import parse_monster_create_form
from backend.models.monster import Monster
from backend.models.user import User
from backend.services.monsters import MonsterNameAlreadyExistsError, update_monster_full_replace_admin

router = APIRouter()

_BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))


def _cr_choices() -> list[str]:
    return ["0", "1/8", "1/4", "1/2"] + [str(n) for n in range(1, 31)]


def _monster_to_form(monster: Monster) -> Dict[str, Any]:
    """
    Convert an ORM Monster into the `form` dict expected by monsters/new.html.
    Keep keys aligned with the create form field names.
    """
    form: Dict[str, Any] = {}

    # Scalars
    form["name"] = monster.name
    form["size"] = monster.size
    form["main_type"] = monster.main_type
    form["subtype"] = monster.subtype or ""
    form["alignment"] = monster.alignment
    form["challenge_rating"] = str(monster.challenge_rating).rstrip("0").rstrip(".") if monster.challenge_rating is not None else ""
    form["xp_override"] = "" if monster.xp_override is None else str(monster.xp_override)
    form["armor_class_text"] = monster.armor_class_text
    form["hit_points"] = str(monster.hit_points)
    form["hit_points_dice"] = monster.hit_points_dice
    form["passive_perception"] = str(monster.passive_perception)
    form["telepathy_range"] = "" if monster.telepathy_range is None else str(monster.telepathy_range)
    form["backstory"] = monster.backstory or ""

    # Ability scores (stored as columns)
    form["ability_scores.STR"] = str(monster.str_score)
    form["ability_scores.DEX"] = str(monster.dex_score)
    form["ability_scores.CON"] = str(monster.con_score)
    form["ability_scores.INT"] = str(monster.int_score)
    form["ability_scores.WIS"] = str(monster.wis_score)
    form["ability_scores.CHA"] = str(monster.cha_score)

    # Saving throws / skills (JSON columns)
    st = monster.saving_throw_proficiencies or {}
    for ab, bonus in (st.get("bonuses") or {}).items():
        form[f"saving_throws.bonuses.{ab}"] = str(bonus)

    sk = monster.skill_proficiencies or {}
    for name, bonus in (sk.get("bonuses") or {}).items():
        form[f"skills.bonuses.{name}"] = str(bonus)

    # JSON blocks (lists of {name,text})
    form["traits_json"] = json.dumps(monster.traits or [])
    form["actions_json"] = json.dumps(monster.actions or [])
    form["reactions_json"] = json.dumps(monster.reactions or [])
    form["legendary_actions_json"] = json.dumps(monster.legendary_actions or [])

    # Newline lists
    form["lair_actions_text"] = "\n".join(monster.lair_actions or [])
    form["regional_effects_text"] = "\n".join(monster.regional_effects or [])

    # Indexed rows
    for i, m in enumerate(monster.movements or []):
        form[f"movement[{i}].type"] = m.movement_type
        form[f"movement[{i}].speed"] = str(m.speed)
        form[f"movement[{i}].hover"] = "on" if m.hover else ""

    for i, s in enumerate(monster.senses or []):
        form[f"senses[{i}].sense"] = s.sense
        form[f"senses[{i}].range"] = str(s.range)

    for i, lang in enumerate(monster.languages or []):
        form[f"languages[{i}].language"] = lang.language

    for i, d in enumerate(monster.damage_resistances or []):
        form[f"damage_resistances[{i}].type"] = d.damage_type
    for i, d in enumerate(monster.damage_immunities or []):
        form[f"damage_immunities[{i}].type"] = d.damage_type
    for i, d in enumerate(monster.damage_vulnerabilities or []):
        form[f"damage_vulnerabilities[{i}].type"] = d.damage_type

    for i, c in enumerate(monster.condition_immunities or []):
        form[f"condition_immunities[{i}].condition"] = c.condition

    return form


def _render_edit_form(
    request: Request,
    *,
    monster: Monster,
    form: Dict[str, Any],
    field_errors: Dict[str, list[str]],
    global_errors: list[str],
) -> HTMLResponse:
    context = {
        "request": request,
        "actor_role": "admin",
        "page_title": "Edit Monster",
        "form_action": f"/monsters/{monster.id}/edit",
        "submit_button_text": "Save changes",
        "enums": {
            "Size": [e.value for e in Size],
            "Alignment": [e.value for e in Alignment],
            "CR": _cr_choices(),
            "AbilityScores": list(range(1, 31)),
            "MovementType": [e.value for e in MovementType],
            "Sense": [e.value for e in Sense],
            "Language": [e.value for e in Language],
            "DamageType": [e.value for e in DamageType],
            "Condition": [e.value for e in Condition],
            "Ability": [e.value for e in Ability],
            "Skill": [e.value for e in Skill],
        },
        "form": form,
        "field_errors": field_errors,
        "global_errors": global_errors,
    }
    return templates.TemplateResponse("monsters/new.html", context)


@router.get("/monsters/{monster_id}/edit", response_class=HTMLResponse)
async def edit_monster_form(
    request: Request,
    monster_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(admin_only),  # Authorization only; returned User not needed
):
    stmt = (
        select(Monster)
        .options(
            selectinload(Monster.movements),
            selectinload(Monster.senses),
            selectinload(Monster.languages),
            selectinload(Monster.damage_immunities),
            selectinload(Monster.damage_resistances),
            selectinload(Monster.damage_vulnerabilities),
            selectinload(Monster.condition_immunities),
        )
        .where(Monster.id == monster_id)
    )
    result = await db.execute(stmt)
    monster = result.scalar_one_or_none()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")

    return _render_edit_form(
        request,
        monster=monster,
        form=_monster_to_form(monster),
        field_errors={},
        global_errors=[],
    )


@router.post("/monsters/{monster_id}/edit", response_class=HTMLResponse)
async def edit_monster_post(
    request: Request,
    monster_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(admin_only),  # Authorization only; returned User not needed
):
    # Load monster (so we can re-render with prefill on errors too)
    stmt = (
        select(Monster)
        .options(
            selectinload(Monster.movements),
            selectinload(Monster.senses),
            selectinload(Monster.languages),
            selectinload(Monster.damage_immunities),
            selectinload(Monster.damage_resistances),
            selectinload(Monster.damage_vulnerabilities),
            selectinload(Monster.condition_immunities),
        )
        .where(Monster.id == monster_id)
    )
    result = await db.execute(stmt)
    monster = result.scalar_one_or_none()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")

    form_data = await request.form()

    # actor_role is "admin" (this keeps create-form validation aligned)
    payload, field_errors, global_errors, raw_form = parse_monster_create_form(
        form_data,
        actor_role="admin",
    )

    if payload is None:
        return _render_edit_form(
            request,
            monster=monster,
            form=raw_form,
            field_errors=field_errors,
            global_errors=global_errors,
        )

    try:
        await update_monster_full_replace_admin(
            monster=monster,
            payload=payload,
            session=db,
        )
    except MonsterNameAlreadyExistsError:
        field_errors.setdefault("name", []).append("A monster with this name already exists")
        return _render_edit_form(
            request,
            monster=monster,
            form=raw_form,
            field_errors=field_errors,
            global_errors=global_errors,
        )

    return RedirectResponse(
        url=f"/monsters/{monster.id}?success=updated",
        status_code=status.HTTP_303_SEE_OTHER,
    )