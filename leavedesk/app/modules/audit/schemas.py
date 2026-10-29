import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    acting_for_id: uuid.UUID | None
    action: str
    target_type: str
    target_id: str | None
    detail: dict[str, Any]
    ip: str | None
    at: datetime
