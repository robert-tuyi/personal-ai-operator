from pydantic import BaseModel


class IncomingMessage(BaseModel):
    """A message we might draft a reply to."""

    id: str = ""
    sender: str = ""
    subject: str = ""
    body: str = ""


class DraftReply(BaseModel):
    """A proposed reply. Drafting is not an outbound action — *sending* it is, and that
    goes through the approval chokepoint (see app/core/approval.py)."""

    message_id: str
    to: str  # who the reply goes to — required by the SEND_EMAIL executor's payload
    subject: str
    body: str
