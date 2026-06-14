from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment / .env. Never hardcode secrets."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_url: str = "http://localhost:8000"

    database_url: str = "sqlite:///./dev.db"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""

    # Where Google redirects back after consent. Must exactly match an Authorized redirect
    # URI in the Google Cloud OAuth client. Defaults to the local dev callback.
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"

    # Signs the session cookie that carries the logged-in user's identity. MUST be set to a
    # long random value in any real deployment — the default is for local dev only.
    session_secret: str = "dev-insecure-change-me"

    # OAuth scopes we request: Gmail read + send, Calendar read + events, plus the OpenID
    # scopes that identify the user. Space-separated, as Google expects.
    google_oauth_scopes: str = (
        "openid email profile "
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/gmail.send "
        "https://www.googleapis.com/auth/calendar.readonly "
        "https://www.googleapis.com/auth/calendar.events"
    )

    # Which LLM provider to use: "anthropic" (default) or "openai". The model pair below
    # for the selected provider applies; the other provider's settings are ignored.
    llm_provider: str = "anthropic"

    # Model selection — cheap by default, quality only where output is the point.
    # See CLAUDE.md "Cost discipline" and the claude-api reference for current IDs.
    model_cheap: str = "claude-haiku-4-5-20251001"
    model_quality: str = "claude-sonnet-4-6"

    # OpenAI equivalents, used when llm_provider == "openai". Overridable via env.
    openai_model_cheap: str = "gpt-4o-mini"
    openai_model_quality: str = "gpt-4o"


@lru_cache
def get_settings() -> Settings:
    return Settings()
