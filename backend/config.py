"""
ScholarClaw — Application Configuration
Pydantic BaseSettings reads from .env automatically.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Central application settings — every module imports `settings`."""

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Groq (LLM Provider) ────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── External services ─────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    ARMORIQ_API_KEY: str = ""

    # ── Frontend ──────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def _get_settings() -> Settings:
    return Settings()


# Singleton used throughout the app: `from config import settings`
settings: Settings = _get_settings()
