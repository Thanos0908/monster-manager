from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_303_SEE_OTHER
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import SESSION_COOKIE_NAME, require_authenticated
from backend.core.database import get_session
from backend.core.security import hash_password, verify_password
from backend.enums.user_roles import UserRole
from backend.models.session import Session as DBSession
from backend.models.user import User

router = APIRouter(tags=["profile"])

# SSR templates (local to avoid importing app.py and creating circular imports)
_BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user=Depends(require_authenticated),
    success: str | None = None,
    error: str | None = None,
):
    # Success messages
    if success == "profile":
        success_message = "Profile updated."
    elif success == "password":
        success_message = "Password updated."
    else:
        success_message = None

    # Error messages
    if error == "username_taken":
        error_message = "That username is already taken."
    elif error == "password_mismatch":
        error_message = "Passwords do not match."
    elif error == "password_too_short":
        error_message = "Password must be at least 12 characters."
    elif error == "current_password_invalid":
        error_message = "Current password is incorrect."
    elif error == "delete_confirm_required":
        error_message = "Please confirm you want to delete your account."
    elif error == "cannot_delete_last_admin":
        error_message = "You are the last admin. Create another admin before deleting this account."
    else:
        error_message = None

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "current_user": current_user,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


@router.post("/profile")
async def update_profile(
    name: str = Form(""),
    username: str = Form(""),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_authenticated),
):
    # Normalize inputs
    new_name = name.strip() or None
    # Username is optional in DB; empty input clears it.
    new_username = username.strip() or None

    try:
        # Reload the user in this session (safe pattern for updates)
        result = await session.execute(select(User).where(User.id == current_user.id))
        user = result.scalar_one()

        user.name = new_name
        user.username = new_username

        await session.commit()
    except IntegrityError:
        # Likely username uniqueness violation (or email, but we aren't editing email here)
        await session.rollback()
        return RedirectResponse(
            url="/profile?error=username_taken",
            status_code=HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/profile?success=profile",
        status_code=HTTP_303_SEE_OTHER,
    )


@router.post("/profile/password")
async def update_password(
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_password: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_authenticated),
):
    if new_password != confirm_password:
        return RedirectResponse(
            "/profile?error=password_mismatch",
            status_code=HTTP_303_SEE_OTHER,
        )

    if len(new_password.strip()) < 12:
        return RedirectResponse(
            "/profile?error=password_too_short",
            status_code=HTTP_303_SEE_OTHER,
        )

    # Reload the user inside *this* session (same pattern as update_profile)
    result = await session.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()

    # User already has a password → require current password
    if user.hashed_password:
        if not current_password or not verify_password(current_password, user.hashed_password):
            return RedirectResponse(
                "/profile?error=current_password_invalid",
                status_code=HTTP_303_SEE_OTHER,
            )

    user.hashed_password = hash_password(new_password)
    await session.commit()

    return RedirectResponse(
        "/profile?success=password",
        status_code=HTTP_303_SEE_OTHER,
    )


@router.post("/profile/delete")
async def delete_own_account(
    confirm: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_authenticated),
):
    # Require checkbox confirmation
    if confirm != "on":
        return RedirectResponse(
            url="/profile?error=delete_confirm_required",
            status_code=HTTP_303_SEE_OTHER,
        )

    # Reload user in this DB session
    result = await session.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()

    # Safety: prevent deleting the last admin
    if user.role == UserRole.ADMIN:
        admin_count_result = await session.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
        )
        admin_count = int(admin_count_result.scalar_one() or 0)

        if admin_count <= 1:
            return RedirectResponse(
                url="/profile?error=cannot_delete_last_admin",
                status_code=HTTP_303_SEE_OTHER,
            )

    # Delete all sessions for this user (belt & suspenders; FK CASCADE may also handle it)
    await session.execute(delete(DBSession).where(DBSession.user_id == user.id))

    # Delete the user
    await session.delete(user)
    await session.commit()

    # Clear auth cookie and redirect to login with a success banner
    resp = RedirectResponse(
        url="/login?success=account_deleted",
        status_code=HTTP_303_SEE_OTHER,
    )
    resp.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return resp