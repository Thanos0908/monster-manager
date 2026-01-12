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

router = APIRouter(prefix="/auth/github", tags=["auth-oauth"])

_OAUTH_STATE_COOKIE = "oauth_state_github"


def _github_authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        # read:user gives profile; user:email allows retrieving verified email list
        "scope": "read:user user:email",
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


@router.get("/start")
async def github_start():
    settings = get_settings()

    if not (settings.GITHUB_CLIENT_ID and settings.GITHUB_REDIRECT_URI and settings.OAUTH_STATE_SECRET):
        return RedirectResponse(url="/login?error=oauth_not_configured", status_code=HTTP_303_SEE_OTHER)

    state = make_state_token(settings.OAUTH_STATE_SECRET, ttl_seconds=600)
    url = _github_authorize_url(settings.GITHUB_CLIENT_ID, settings.GITHUB_REDIRECT_URI, state)

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
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    settings = get_settings()

    if not (
        settings.GITHUB_CLIENT_ID
        and settings.GITHUB_CLIENT_SECRET
        and settings.GITHUB_REDIRECT_URI
        and settings.OAUTH_STATE_SECRET
    ):
        return RedirectResponse(url="/login?error=oauth_not_configured", status_code=HTTP_303_SEE_OTHER)

    cookie_state = request.cookies.get(_OAUTH_STATE_COOKIE)
    if not code or not state or not cookie_state:
        return RedirectResponse(url="/login?error=oauth_failed", status_code=HTTP_303_SEE_OTHER)

    # Double-submit check + signature/expiry check
    if state != cookie_state:
        resp = RedirectResponse(url="/login?error=oauth_state_invalid", status_code=HTTP_303_SEE_OTHER,)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp
    if not verify_state_token(settings.OAUTH_STATE_SECRET, state):
        resp = RedirectResponse(url="/login?error=oauth_state_expired", status_code=HTTP_303_SEE_OTHER,)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    # Exchange code for access token + fetch profile/emails
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
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

            user_resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            user_resp.raise_for_status()
            gh_user = user_resp.json()

            raw_id = gh_user.get("id")
            if raw_id is None:
                resp = RedirectResponse(
                    url="/login?error=oauth_failed",
                    status_code=HTTP_303_SEE_OTHER,
                )
                resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
                return resp

            gh_id = str(raw_id)
            name = gh_user.get("name") or gh_user.get("login")

            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            emails_resp.raise_for_status()
            emails = emails_resp.json()  # list[{email, primary, verified, visibility}]

    except (httpx.HTTPError, ValueError, TypeError):
        resp = RedirectResponse(url="/login?error=oauth_failed", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    email = None
    if isinstance(emails, list):
        # Prefer primary+verified, then any verified, then first.
        primary_verified = next((e for e in emails if e.get("primary") and e.get("verified")), None)
        any_verified = next((e for e in emails if e.get("verified")), None)
        chosen = primary_verified or any_verified or (emails[0] if emails else None)
        if chosen:
            email = chosen.get("email")

    if not email:
        resp = RedirectResponse(url="/login?error=github_email_required", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    try:
        user = await get_or_create_user_for_oauth(
            session,
            provider="github",
            provider_id=gh_id,
            email=email,
            name=name,
        )
    except OAuthEmailConflictError:
        resp = RedirectResponse(url="/login?error=oauth_email_conflict", status_code=HTTP_303_SEE_OTHER)
        resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
        return resp

    # Create your normal DB session + cookie
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
    # clear oauth temp cookie
    resp.delete_cookie(key=_OAUTH_STATE_COOKIE, path="/")
    resp.delete_cookie(key="oauth_state", path="/")  # legacy cookie cleanup (pre provider-specific state)
    return resp