from __future__ import annotations
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_303_SEE_OTHER
from backend.authorization.dependencies import SESSION_COOKIE_NAME
from backend.core.config import get_settings
from backend.core.database import get_session
from backend.core.oauth_state import make_state_token, verify_state_token
from backend.services.auth import create_db_session
from backend.services.oauth_link import OAuthEmailConflictError, get_or_create_user_for_oauth

router = APIRouter(prefix="/auth/google", tags=["auth-oauth"])

_OAUTH_STATE_COOKIE = "oauth_state_google"


def _google_authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        # helps ensure a refresh token in real apps; harmless in dev
        "access_type": "offline",
        # keeps dev testing predictable
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


@router.get("/start")
async def google_start():
    settings = get_settings()

    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_REDIRECT_URI and settings.OAUTH_STATE_SECRET):
        return RedirectResponse(url="/login?error=oauth_not_configured", status_code=HTTP_303_SEE_OTHER)

    state = make_state_token(settings.OAUTH_STATE_SECRET, ttl_seconds=600)
    url = _google_authorize_url(settings.GOOGLE_CLIENT_ID, settings.GOOGLE_REDIRECT_URI, state)

    resp = RedirectResponse(url=url, status_code=HTTP_303_SEE_OTHER)
    resp.set_cookie(
        key=_OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
        max_age=600,
    )
    return resp


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    settings = get_settings()

    if not (
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
        and settings.GOOGLE_REDIRECT_URI
        and settings.OAUTH_STATE_SECRET
    ):
        return RedirectResponse(url="/login?error=oauth_not_configured", status_code=HTTP_303_SEE_OTHER)

    cookie_state = request.cookies.get(_OAUTH_STATE_COOKIE)
    if not code or not state or not cookie_state:
        return RedirectResponse(url="/login?error=oauth_failed", status_code=HTTP_303_SEE_OTHER)

    if state != cookie_state:
        resp = RedirectResponse(url="/login?error=oauth_state_invalid", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    if not verify_state_token(settings.OAUTH_STATE_SECRET, state):
        resp = RedirectResponse(url="/login?error=oauth_state_expired", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    try:
        # Exchange code for tokens
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()
            token_json = token_resp.json()
            access_token = token_json.get("access_token")

            if not access_token:
                resp = RedirectResponse(url="/login?error=oauth_failed", status_code=HTTP_303_SEE_OTHER)
                resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
                return resp

            # Get user info (OpenID Connect)
            userinfo_resp = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            userinfo_resp.raise_for_status()
            info = userinfo_resp.json()

    except (httpx.HTTPError, ValueError, TypeError):
        resp = RedirectResponse(url="/login?error=oauth_failed", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    google_sub = info.get("sub")
    email = info.get("email")
    name = info.get("name") or info.get("given_name")

    # Google often includes email_verified in userinfo; require it if present.
    email_verified = info.get("email_verified")
    if email_verified is False:
        resp = RedirectResponse(url="/login?error=google_email_unverified", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    if not google_sub:
        resp = RedirectResponse(url="/login?error=oauth_failed", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    if not email:
        resp = RedirectResponse(url="/login?error=google_email_required", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    try:
        user = await get_or_create_user_for_oauth(
            session,
            provider="google",
            provider_id=str(google_sub),
            email=email,
            name=name,
        )
    except OAuthEmailConflictError:
        resp = RedirectResponse(url="/login?error=oauth_email_conflict", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

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
    resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
    return resp