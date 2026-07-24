from datetime import datetime

from pydantic import BaseModel


class MemoryItem(BaseModel):
    """A stored fragment of the user's own past behavior (e.g. a sent reply), retrieved to
    give brief/draft generation relevant context. Written only after an outbound action has
    actually executed — never from a draft or proposal (see services/memory.py)."""

    id: str
    content: str
    source: str  # what produced this memory, e.g. "sent_email"
    created_at: datetime
