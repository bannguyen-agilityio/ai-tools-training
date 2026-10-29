import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OutboxEntryOut(BaseModel):
    """No subject, body or payload: HR needs to see the failure, not the content."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    to_address: str
    template: str
    status: str
    attempts: int
    last_error: str | None
    created_at: datetime
