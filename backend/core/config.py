"""Application configuration loader. 
Reads environment variables and exposes 
them via a cached Settings object."""

from functools import lru_cache  
from pathlib import Path
import os
# We check if the .env file exists and then we import it if it does
# For dev use not production.
try:
    from dotenv import load_dotenv  
    ROOT_DIR = Path(__file__).resolve().parents[2] # D&D/monster_manager/
    load_dotenv(ROOT_DIR / ".env")
except Exception:
    pass


class Settings:
    """Minimal settings holder for early boot. Expand later."""
    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-not-secret")
        self.GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
        self.GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
        self.GITHUB_REDIRECT_URI: str = os.getenv("GITHUB_REDIRECT_URI", "")
        self.OAUTH_STATE_SECRET: str = os.getenv("OAUTH_STATE_SECRET", "")
        self.GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
        self.GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")
        self.COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true" # Whether auth cookies require HTTPS (True in production)


# lru_cached ensures this function runs only once per process.
# The first time get_settings() is called, it creates a Settings object.
# All calls after that return the same cached instance instead of rerunning 
# the function to read the env vars again.
@lru_cache
def get_settings() -> Settings:
    """Cached singleton-ish settings instance."""
    return Settings()
