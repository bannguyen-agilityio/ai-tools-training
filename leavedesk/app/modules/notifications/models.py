import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Notification(Base):
    __tablename__ = "notification"
    __table_args__ = (
        Index("ix_notification_employee_read_created", "employee_id", "read_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)
    link: Mapped[str] = mapped_column(String)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    dedupe_key: Mapped[str] = mapped_column(String, unique=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
