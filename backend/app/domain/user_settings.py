from enum import StrEnum

from pydantic import BaseModel


class Tone(StrEnum):
    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"


class UserSettings(BaseModel):
    """A user's own preferences: working hours, timezone, drafting tone, VIP contacts, and
    escalation rules. Stored only — nothing in brief/drafts/follow-ups reads or acts on
    these yet; that's a separate, later decision.

    onboarding_completed gates the one-time onboarding flow (frontend redirects here until
    it's true)."""

    work_hours_start: str = "09:00"  # "HH:MM", 24-hour
    work_hours_end: str = "17:00"
    timezone: str = "UTC"  # IANA name, e.g. "Europe/Helsinki"
    tone: Tone = Tone.CASUAL
    vip_contacts: list[str] = []  # email addresses
    escalation_rules: list[str] = []  # free-text rules, not yet interpreted by anything
    onboarding_completed: bool = False
