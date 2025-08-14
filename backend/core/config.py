from functools import lru_cache  
from pathlib import Path
import os
# We check if the .env file exists and then we import it if it does
# For dev use not production.
try:
    from dotenv import load_dotenv  
    ROOT_DIR = Path(__file__).resolve().parents[2]  
    load_dotenv(ROOT_DIR / ".env")
except Exception:
    pass


class Settings:
    """Minimal settings holder for early boot. Expand later."""
    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-not-secret")


# lru_cached ensurs this function runs only once per process.
# The first time get_settings() is called, it creates a Settings object.
# All calls after that return the same cached instance instead of rerruning 
# the function to read the env vars again.
@lru_cache
def get_settings() -> Settings:
    """Cached singleton-ish settings instance."""
    return Settings()
