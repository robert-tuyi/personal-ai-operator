"""Persistence for user preferences (app/domain/user_settings.py).

Plain functions over a SQLModel session (no HTTP), so they're testable in isolation. The
table is owner-scoped (ADR 0003).
"""

from datetime import UTC, datetime

from sqlmodel import Session

from app.db.models import UserSettingsRow
from app.domain.user_settings import UserSettings


def get_user_settings(session: Session, *, owner_id: str) -> UserSettings:
    """The stored settings for an owner, or defaults if none have been saved yet."""
    row = session.get(UserSettingsRow, owner_id)
    if row is None:
        return UserSettings()
    return UserSettings(
        work_hours_start=row.work_hours_start,
        work_hours_end=row.work_hours_end,
        timezone=row.timezone,
        tone=row.tone,
        vip_contacts=row.vip_contacts,
        escalation_rules=row.escalation_rules,
        onboarding_completed=row.onboarding_completed,
    )


def save_user_settings(
    session: Session, *, owner_id: str, settings: UserSettings
) -> UserSettings:
    """Upsert the stored settings for an owner."""
    now = datetime.now(UTC)
    row = session.get(UserSettingsRow, owner_id)
    if row is None:
        row = UserSettingsRow(owner_id=owner_id, created_at=now, updated_at=now)

    row.work_hours_start = settings.work_hours_start
    row.work_hours_end = settings.work_hours_end
    row.timezone = settings.timezone
    row.tone = settings.tone.value
    row.vip_contacts = settings.vip_contacts
    row.escalation_rules = settings.escalation_rules
    row.onboarding_completed = settings.onboarding_completed
    row.updated_at = now

    session.add(row)
    session.commit()
    return get_user_settings(session, owner_id=owner_id)
