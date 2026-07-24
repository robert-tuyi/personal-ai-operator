"""Settings fail-fast tests (ADR 0003): refuse to start outside development with an unset
or dev-only-default SESSION_SECRET / TOKEN_ENCRYPTION_KEY."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_allows_insecure_defaults_in_development():
    Settings(app_env="development")  # must not raise


def test_refuses_default_session_secret_outside_development():
    with pytest.raises(ValidationError, match="SESSION_SECRET"):
        Settings(app_env="production", token_encryption_key="a-real-looking-key-value")


def test_refuses_blank_session_secret_outside_development():
    with pytest.raises(ValidationError, match="SESSION_SECRET"):
        Settings(
            app_env="production", session_secret="", token_encryption_key="a-real-key-value"
        )


def test_refuses_default_token_encryption_key_outside_development():
    with pytest.raises(ValidationError, match="TOKEN_ENCRYPTION_KEY"):
        Settings(app_env="production", session_secret="a-real-looking-secret")


def test_refuses_blank_token_encryption_key_outside_development():
    with pytest.raises(ValidationError, match="TOKEN_ENCRYPTION_KEY"):
        Settings(
            app_env="production", session_secret="a-real-looking-secret", token_encryption_key=""
        )


def test_allows_real_looking_values_outside_development():
    Settings(
        app_env="production",
        session_secret="a-real-looking-secret",
        token_encryption_key="a-real-looking-key-value",
    )  # must not raise
