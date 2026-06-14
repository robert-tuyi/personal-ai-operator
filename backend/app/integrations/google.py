"""Gmail + Google Calendar integration.

Read helpers fetch context for the brief and drafts. The write helpers (_send_email,
_create_event) are the *executors* for approved actions — they are registered with the
approval chokepoint and must only ever be invoked through it, never called directly.
"""

from app.core import approval
from app.domain.actions import ActionType


def list_recent_messages(limit: int = 20) -> list[dict]:
    # TODO: fetch via Gmail API using the user's OAuth token. Returns [] until wired.
    return []


def todays_events() -> list[dict]:
    # TODO: fetch via Calendar API. Returns [] until wired.
    return []


def _send_email(payload: dict) -> None:
    # TODO: send via Gmail API. Invoked only by approval.execute_approved.
    raise NotImplementedError("Gmail send not wired yet")


def _create_event(payload: dict) -> None:
    # TODO: create via Calendar API. Invoked only by approval.execute_approved.
    raise NotImplementedError("Calendar create not wired yet")


def register_action_executors() -> None:
    """Wire side-effecting executors into the approval chokepoint. Called at app startup."""
    approval.register_executor(ActionType.SEND_EMAIL, _send_email)
    approval.register_executor(ActionType.CREATE_CALENDAR_EVENT, _create_event)
