from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import admin_only
from backend.core.database import get_session
from backend.models.monster import Monster
from backend.models.user import User
from backend.services.monsters import MonsterNotFoundError, delete_monster_admin

router = APIRouter()

_BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))


@router.get("/monsters/{monster_id}/delete", response_class=HTMLResponse)
async def delete_monster_confirm(
    request: Request,
    monster_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(admin_only),  # Authorization only; returned User not needed
):
    """Admin-only SSR delete confirm screen."""
    result = await db.execute(select(Monster).where(Monster.id == monster_id))
    monster = result.scalar_one_or_none()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")

    return templates.TemplateResponse(
        request,
        "monsters/delete_confirm.html",
        {"monster": monster},
    )


@router.post("/monsters/{monster_id}/delete")
async def delete_monster_post(
    monster_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(admin_only),  # Authorization only; returned User not needed
):
    """Admin-only delete action. Redirects to list with a success banner."""
    try:
        await delete_monster_admin(monster_id=monster_id, session=db)
    except MonsterNotFoundError:
        raise HTTPException(status_code=404, detail="Monster not found")

    return RedirectResponse(
        url="/monsters?success=deleted",
        status_code=status.HTTP_303_SEE_OTHER,
    )
