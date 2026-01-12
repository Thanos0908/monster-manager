from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import dm_or_admin
from backend.core.database import get_session
from backend.forms.monsters import parse_monster_create_form
from backend.models.user import User
from backend.services.monsters import MonsterNameAlreadyExistsError, create_monster
from backend.enums.monster_enums import (
    Size,
    Alignment,
    MovementType,
    Sense,
    Language,
    DamageType,
    Condition,
    Ability,
    Skill,
)

router = APIRouter()

_BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))


def _cr_choices() -> list[str]:
    return ["0", "1/8", "1/4", "1/2"] + [str(n) for n in range(1, 31)]


def _render_new_form(
    request: Request,
    *,
    actor_role: str,
    form: dict,
    field_errors: dict,
    global_errors: list,
) -> HTMLResponse:
    """
    Render the Monster Create SSR form.
    Important:
    - After a failed DB operation / rollback, ORM objects may be expired.
    - Accessing ORM attributes can trigger lazy-load IO and raise MissingGreenlet.
    - Therefore this render helper uses only plain primitives (actor_role, booleans, etc.).
    """
    is_admin = actor_role == "admin"

    context = {
        "request": request,
        "actor_role": actor_role,
        "submit_button_text": "Create official monster" if is_admin else "Submit monster for moderation",
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


@router.get("/monsters/new", response_class=HTMLResponse)
async def new_monster_form(
    request: Request,
    current_user: User = Depends(dm_or_admin),
):
    actor_role = str(getattr(current_user.role, "value", current_user.role)).lower()
    return _render_new_form(
        request,
        actor_role=actor_role,
        form={},
        field_errors={},
        global_errors=[],
    )


@router.post("/monsters/new", response_class=HTMLResponse)
async def create_monster_post(
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(dm_or_admin),
):
    # Compute once; do not re-read ORM attributes after rollback.
    actor_role = str(getattr(current_user.role, "value", current_user.role)).lower()

    form_data = await request.form()
    payload, field_errors, global_errors, raw_form = parse_monster_create_form(
        form_data,
        actor_role=actor_role,
    )

    if payload is None:
        return _render_new_form(
            request,
            actor_role=actor_role,
            form=raw_form,
            field_errors=field_errors,
            global_errors=global_errors,
        )

    try:
        monster = await create_monster(actor=current_user, payload=payload, session=db)
    except MonsterNameAlreadyExistsError:
        field_errors.setdefault("name", []).append("A monster with this name already exists")
        return _render_new_form(
            request,
            actor_role=actor_role,
            form=raw_form,
            field_errors=field_errors,
            global_errors=global_errors,
        )

    if actor_role == "admin":
        return RedirectResponse(
            url=f"/monsters/{monster.id}?success=created",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/dashboard?success=monster_created_pending",
        status_code=status.HTTP_303_SEE_OTHER,
    )