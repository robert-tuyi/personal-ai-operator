"""User settings service tests — defaults, upsert semantics."""

from app.domain.user_settings import Tone, UserSettings
from app.services.user_settings import get_user_settings, save_user_settings


def test_get_returns_defaults_when_unset(session):
    settings = get_user_settings(session, owner_id="sub-123")
    assert settings == UserSettings()


def test_save_then_get_round_trips(session):
    saved = save_user_settings(
        session,
        owner_id="sub-123",
        settings=UserSettings(
            work_hours_start="08:00",
            work_hours_end="16:00",
            timezone="Europe/Helsinki",
            tone=Tone.DIRECT,
            vip_contacts=["boss@example.com"],
            escalation_rules=["Notify immediately if from a VIP contact"],
            onboarding_completed=True,
        ),
    )
    assert saved.timezone == "Europe/Helsinki"
    assert saved.tone == Tone.DIRECT
    assert saved.vip_contacts == ["boss@example.com"]
    assert saved.onboarding_completed is True

    fetched = get_user_settings(session, owner_id="sub-123")
    assert fetched == saved


def test_save_upserts_existing_row(session):
    save_user_settings(
        session, owner_id="sub-123", settings=UserSettings(timezone="UTC")
    )
    updated = save_user_settings(
        session, owner_id="sub-123", settings=UserSettings(timezone="America/New_York")
    )
    assert updated.timezone == "America/New_York"

    fetched = get_user_settings(session, owner_id="sub-123")
    assert fetched.timezone == "America/New_York"


def test_settings_are_owner_scoped(session):
    save_user_settings(
        session, owner_id="sub-a", settings=UserSettings(timezone="UTC")
    )
    save_user_settings(
        session, owner_id="sub-b", settings=UserSettings(timezone="Europe/Helsinki")
    )
    assert get_user_settings(session, owner_id="sub-a").timezone == "UTC"
    assert get_user_settings(session, owner_id="sub-b").timezone == "Europe/Helsinki"
