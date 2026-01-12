from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import require_authenticated, monster_filter_for_user
from backend.core.database import get_session
from backend.models.monster import Monster
from backend.models.user import User


router = APIRouter()

_BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))


@router.get("/monsters/{monster_id}", response_class=HTMLResponse)
async def monster_detail(
    request: Request,
    monster_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_authenticated),
):
    stmt = (
        select(Monster)
        .options(selectinload(Monster.owner),
                 selectinload(Monster.movements), 
                 selectinload(Monster.senses),
                 selectinload(Monster.languages),
                 selectinload(Monster.damage_immunities),
                 selectinload(Monster.damage_resistances),
                 selectinload(Monster.damage_vulnerabilities),
                 selectinload(Monster.condition_immunities),)
        .where(
            Monster.id == monster_id,
            monster_filter_for_user(current_user),
        )
    )
    result = await db.execute(stmt)
    monster = result.scalar_one_or_none()

    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")

    return templates.TemplateResponse(
        request,
        "monsters/detail.html",
        {
            "current_user": current_user,
            "monster": monster,
            "success": request.query_params.get("success"),
        },
    )
