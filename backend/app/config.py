from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment / .env. Never hardcode secrets."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_url: str = "http://localhost:8000"

    database_url: str = "sqlite:///./dev.db"

    anthropic_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""

    # Model selection — cheap by default, quality only where output is the point.
    # See CLAUDE.md "Cost discipline" and the claude-api reference for current IDs.
    model_cheap: str = "claude-haiku-4-5-20251001"
    model_quality: str = "claude-sonnet-4-6"


@lru_cache
def get_settings() -> Settings:
    return Settings()
