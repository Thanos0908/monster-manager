from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import admin_only
from backend.core.database import get_session
from backend.enums.user_roles import UserRole
from backend.models.user import User

router = APIRouter(tags=["admin"])

# SSR templates (keep it local to avoid importing app.py and creating circular imports)
_BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))


_SUCCESS_MESSAGES: dict[str, str] = {
    "approved": "User approved.",
    "role_updated": "Role updated.",
    "deleted": "User deleted.",
}

_ERROR_MESSAGES: dict[str, str] = {
    "invalid_role": "Invalid role selected.",
    "user_not_found": "User not found.",
    "cannot_change_self": "You can't change your own role.",
    "role_change_requires_approval": "Approve the user before changing roles.",
    "cannot_downgrade_admin": "Admin users cannot be downgraded.",
    "cannot_delete_admin": "Admin users cannot be deleted.",
}


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(admin_only),
    success: str | None = None,
    error: str | None = None,
):
    success_message = _SUCCESS_MESSAGES.get(success) if success else None
    error_message = _ERROR_MESSAGES.get(error) if error else None

    result = await session.execute(
        select(User).order_by(User.is_approval_pending.desc(), User.email.asc())
    )
    users = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "admin_users.html",
        {
            "current_user": current_user,
            "users": users,
            "success_message": success_message,
            "error_message": error_message,
            "roles": list(UserRole),  # for role dropdown
        },
    )


@router.post("/admin/users/{user_id}/approve")
async def approve_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(admin_only),  # Authorization only; returned User not needed 
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return RedirectResponse(
            url="/admin/users?error=user_not_found",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if user.is_approval_pending:
        user.is_approval_pending = False
        await session.commit()

    return RedirectResponse(
        url="/admin/users?success=approved",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/users/{user_id}/role")
async def change_user_role(
    user_id: uuid.UUID,
    role: str = Form(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(admin_only),
):
    # Validate role string first
    try:
        new_role = UserRole(role)  # expects "ADMIN" / "DM" / "PLAYER"
    except ValueError:
        return RedirectResponse(
            url="/admin/users?error=invalid_role",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return RedirectResponse(
            url="/admin/users?error=user_not_found",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # role changes only after approval
    if user.is_approval_pending:
        return RedirectResponse(
            url="/admin/users?error=role_change_requires_approval",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # admins are permanent (cannot downgrade an ADMIN)
    if user.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
        return RedirectResponse(
            url="/admin/users?error=cannot_downgrade_admin",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # Extra safety: prevent admin from locking themselves out (explicit intent)
    if user_id == current_user.id and new_role != UserRole.ADMIN:
        return RedirectResponse(
            url="/admin/users?error=cannot_change_self",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user.role = new_role
    await session.commit()

    return RedirectResponse(
        url="/admin/users?success=role_updated",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/users/{user_id}/delete")
async def delete_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(admin_only),  # Authorization only; returned User not needed
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return RedirectResponse(
            url="/admin/users?error=user_not_found",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # admin users cannot be deleted
    if user.role == UserRole.ADMIN:
        return RedirectResponse(
            url="/admin/users?error=cannot_delete_admin",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    await session.delete(user)
    await session.commit()

    return RedirectResponse(
        url="/admin/users?success=deleted",
        status_code=status.HTTP_303_SEE_OTHER,
    )