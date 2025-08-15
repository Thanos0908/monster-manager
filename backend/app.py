from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from pathlib import Path
from backend.core.config import get_settings

# Load settings (cached singleton from config.py)
settings = get_settings()

# Base path for this file → backend/
BASE_DIR = Path(__file__).resolve().parent

# Paths for templates and static files
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create the FastAPI application instance
app = FastAPI()

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

# 4) Home route (server-side rendered HTML)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the base.html page from templates_.
    Args:
        request: Required for Jinja2 template rendering in FastAPI.
    """
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,   # Required for template rendering
            "title": "Monster Manager"  # Example variable passed to template
        }
    )