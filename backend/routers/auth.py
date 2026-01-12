from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from backend.authorization.dependencies import SESSION_COOKIE_NAME
from backend.core.config import get_settings
from backend.core.database import get_session
from backend.schemas.user.user_pydantic_models import UserLogin
from backend.services.auth import (
    InvalidCredentialsError,
    authenticate_local,
    create_db_session,
    delete_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """Local login.
    On success:
      - creates a row in `sessions`
      - sets `session_id` HttpOnly cookie
      - redirects to /dashboard
    Pending users can log in but may have restricted access until approved.
    """
    settings = get_settings()

    # Reuse your schema validation (email normalization, etc.)
    data = UserLogin(email=email, password=password)

    try:
        user = await authenticate_local(db, email=data.email, password=data.password)
    except InvalidCredentialsError:
        return RedirectResponse(
            url="/login?error=invalid_credentials",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    db_sess = await create_db_session(db, user_id=user.id)

    resp: Response = RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(db_sess.id),
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return resp


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        try:
            await delete_session(db, session_id=UUID(session_id))
        except ValueError:
            pass

    resp = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    resp.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
    )
    return resp