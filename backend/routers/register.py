from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_303_SEE_OTHER
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import SESSION_COOKIE_NAME, get_optional_current_user
from backend.core.config import get_settings
from backend.core.database import get_session
from backend.core.security import hash_password
from backend.enums.user_roles import UserRole
from backend.models.user import User
from backend.schemas.user.user_pydantic_models import UserCreateLocal
from backend.services.auth import create_db_session

router = APIRouter(tags=["register"])

# SSR templates (local to avoid importing app.py and creating circular imports)
_BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user=Depends(get_optional_current_user),
    error: str | None = None,
):
    # If already logged in, go straight to dashboard
    if current_user is not None:
        return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)

    if error == "email_taken":
        error_message = "An account with that email already exists."
    elif error == "username_taken":
        error_message = "That username is already taken."
    elif error == "passwords_mismatch":
        error_message = "Passwords do not match."
    elif error == "invalid":
        error_message = "Please check your inputs and try again."
    else:
        error_message = None

    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {
            "error_message": error_message,
        },
    )


@router.post("/register")
async def register(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Local registration (SSR-friendly).
    Creates a new user as:
      - role=PLAYER
      - is_approval_pending=True
    Then auto-logs in (creates DB session + sets cookie) and redirects to /dashboard.
    """
    settings = get_settings()

    # Validate using your existing Pydantic schema (normalizes email, validates username + password rules)
    try:
        data = UserCreateLocal(
            email=email,
            username=username,
            password=password,
            password_confirm=password_confirm,
        )
    except ValidationError as e:
        # Distinguish common case (password mismatch) from general validation.
        msg = str(e).lower()
        if "passwords do not match" in msg:
            return RedirectResponse(
                url="/register?error=passwords_mismatch",
                status_code=HTTP_303_SEE_OTHER,
            )
        return RedirectResponse(
            url="/register?error=invalid",
            status_code=HTTP_303_SEE_OTHER,
        )

    user = User(
        email=data.email,  # already normalized by schema
        username=data.username,
        hashed_password=hash_password(data.password),
        role=UserRole.PLAYER,
        is_approval_pending=True,
    )

    try:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()

        # (DB will enforce uniqueness; we keep messages simple.)
        email_norm = data.email.strip().lower()
        q = await session.execute(User.__table__.select().where(User.email == email_norm))
        existing_by_email = q.first()

        if existing_by_email:
            return RedirectResponse(
                url="/register?error=email_taken",
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url="/register?error=username_taken",
            status_code=HTTP_303_SEE_OTHER,
        )

    # Auto-login: create session row + cookie (same as local login)
    db_sess = await create_db_session(session, user_id=user.id)

    resp: Response = RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(db_sess.id),
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return resp