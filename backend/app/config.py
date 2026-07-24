from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Dev-only insecure defaults (ADR 0003). Public in this repo, so they provide zero security
# once deployed — the validator below refuses to start outside development if either is
# still in use (including left blank, e.g. an empty value in .env).
_INSECURE_SESSION_SECRET = "dev-insecure-change-me"
_INSECURE_TOKEN_ENCRYPTION_KEY = "E5SCWk1BU7BjId6tUZBRXQ7cWv1NvccnH197mL0r060="


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
    session_secret: str = _INSECURE_SESSION_SECRET

    # Encrypts stored Google OAuth tokens at rest (core/crypto.py). MUST be set to a real
    # generated value in any real deployment — the default is for local dev only.
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    token_encryption_key: str = _INSECURE_TOKEN_ENCRYPTION_KEY

    # OAuth scopes we request: Gmail read + send, Calendar read + events, plus the OpenID
    # scopes that identify the user. Space-separated, as Google expects.
    google_oauth_scopes: str = (
        "openid email profile "
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/gmail.send "
        "https://www.googleapis.com/auth/calendar.readonly "
        "https://www.googleapis.com/auth/calendar.events"
    )

    # Which LLM provider to use: "openai" (default) or "anthropic". The model pair below
    # for the selected provider applies; the other provider's settings are ignored.
    llm_provider: str = "openai"

    # Model selection — cheap by default, quality only where output is the point.
    # See CLAUDE.md "Cost discipline" and the claude-api reference for current IDs.
    model_cheap: str = "claude-haiku-4-5-20251001"
    model_quality: str = "claude-sonnet-4-6"

    # OpenAI equivalents, used when llm_provider == "openai". Overridable via env.
    openai_model_cheap: str = "gpt-4o-mini"
    openai_model_quality: str = "gpt-4o"

    # Embeddings (Phase 2 memory layer) always go through OpenAI, regardless of
    # llm_provider — Anthropic has no embeddings API. Requires OPENAI_API_KEY to be set
    # even when llm_provider == "anthropic".
    openai_embedding_model: str = "text-embedding-3-small"

    # Follow-up engine (Phase 3): a sent thread counts as "awaiting reply" once its last
    # message (from the owner) is at least this many days old with no reply.
    followup_stale_after_days: int = 3

    @model_validator(mode="after")
    def _refuse_insecure_defaults_outside_development(self) -> "Settings":
        """ADR 0003: forging a session or decrypting stored OAuth tokens must not be
        possible just because someone forgot to set a real secret in a real deployment."""
        if self.app_env == "development":
            return self

        insecure = []
        if not self.session_secret or self.session_secret == _INSECURE_SESSION_SECRET:
            insecure.append("SESSION_SECRET")
        token_key_insecure = (
            not self.token_encryption_key
            or self.token_encryption_key == _INSECURE_TOKEN_ENCRYPTION_KEY
        )
        if token_key_insecure:
            insecure.append("TOKEN_ENCRYPTION_KEY")

        if insecure:
            raise ValueError(
                f"Refusing to start with app_env={self.app_env!r} while these are unset or "
                f"still the dev-only default: {', '.join(insecure)}. Set real values in the "
                "environment."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
