"""
FastAPI application entrypoint.
Wires routers, templates, static assets, and global exception handling.
"""

from __future__ import annotations
from pathlib import Path
from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler as default_http_exception_handler
from starlette import status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.authorization.dependencies import get_optional_current_user, require_authenticated
from backend.core.config import get_settings
from backend.routers.admin_users import router as admin_users_router
from backend.routers.auth import router as auth_router
from backend.routers.monsters import router as monsters_router
from backend.routers.oauth_github import router as oauth_github_router
from backend.routers.oauth_google import router as oauth_google_router
from backend.routers.profile import router as profile_router
from backend.routers.register import router as register_router


# Load settings (cached singleton from config.py)
settings = get_settings()

# Base path for this file → backend/
BASE_DIR = Path(__file__).resolve().parent

# Paths for templates and static files
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create the FastAPI application instance
app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Global HTTP exception handling.

    SSR behavior:
    - If a protected page raises 401 and the client looks like a browser (Accept includes
      text/html OR is */*), redirect to /login.
    - Otherwise fall back to FastAPI's default exception handler (JSON responses, etc.).
    """
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        accept = (request.headers.get("accept") or "").lower()

        # Browsers usually send "text/html,..."
        # httpx default is "*/*" (we still want SSR redirect in tests)
        if "text/html" in accept or "*/*" in accept or accept == "":
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return await default_http_exception_handler(request, exc)

# Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(admin_users_router)
app.include_router(register_router)
app.include_router(oauth_github_router)
app.include_router(oauth_google_router)
app.include_router(monsters_router)

# 1) Mount static files (e.g., CSS, JS, images) so they can be accessed via /static/*
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 2) Setup template rendering (HTML pages)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# 3) Health check route
@app.get("/health", response_class=JSONResponse)
async def health():
    """
    Health check endpoint.
    Returns:
        status: "ok" if reachable.
        env:
            database_url_set: True if DATABASE_URL is configured in env.
            secret_key_set: True if SECRET_KEY is not the dev default.
    """
    return {
        "status": "ok",
        "env": {
            "database_url_set": bool(settings.DATABASE_URL),
            "secret_key_set": settings.SECRET_KEY != "dev-not-secret",
        },
    }


# 4) Root route: redirect router only
@app.get("/", response_class=HTMLResponse)
async def root(current_user=Depends(get_optional_current_user)):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


# 5) Login page (public landing)
@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: str | None = None,
    success: str | None = None,
    current_user=Depends(get_optional_current_user),
):
    # If already logged in, go straight to dashboard
    if current_user is not None:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    # Success banner mapping
    if success == "account_deleted":
        success_message = "Your account was deleted."
    else:
        success_message = None

    # Error banner mapping
    if error == "invalid_credentials":
        error_message = "Invalid email or password."
    elif error == "github_email_required":
        error_message = (
            "GitHub did not provide an email address. Please enable email access in GitHub "
            "or make an email public/available."
        )
    elif error == "google_email_required":
        error_message = "Google did not provide an email address. Please choose a Google account with an email."
    elif error == "oauth_state_invalid":
        error_message = "OAuth security check failed. Please try again."
    elif error == "oauth_state_expired":
        error_message = "Login took too long. Please try again."
    elif error == "oauth_not_configured":
        error_message = "OAuth is not configured on the server."
    elif error == "oauth_email_conflict":
        error_message = "That email is already linked to a different OAuth account."
    elif error == "oauth_failed":
        error_message = "OAuth login failed. Please try again."
    else:
        error_message = None

    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "error_message": error_message,
            "success_message": success_message,
        },
    )


# 6) Authenticated landing page (post-login home)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user=Depends(require_authenticated),
):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "current_user": current_user,
        },
    )