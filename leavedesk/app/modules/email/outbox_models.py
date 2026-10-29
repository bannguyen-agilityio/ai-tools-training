import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

NOW = text("now()")


class EmailOutbox(Base):
    """Written in the caller's transaction (outbox pattern); drained by app.jobs.drain_outbox."""

    __tablename__ = "email_outbox"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','sent','failed','mocked')", name="ck_email_outbox_status"
        ),
        Index("ix_email_outbox_status_next_try", "status", "next_try_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    recipient_employee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    to_address: Mapped[str] = mapped_column(String)
    template: Mapped[str] = mapped_column(String)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    subject: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text)
    dedupe_key: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String, server_default="pending")
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    next_try_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)
