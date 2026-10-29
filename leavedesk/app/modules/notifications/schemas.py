import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    title: str
    body: str
    link: str
    request_id: uuid.UUID | None
    read_at: datetime | None
    created_at: datetime


class NotificationList(BaseModel):
    unread_count: int
    items: list[NotificationOut]
