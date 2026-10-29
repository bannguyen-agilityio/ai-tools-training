import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

UUID_DEFAULT = text("gen_random_uuid()")
NOW = text("now()")


class UserIdentity(Base):
    __tablename__ = "user_identity"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str | None] = mapped_column(String)
    provider_subject: Mapped[str | None] = mapped_column(String)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)


class OneTimeToken(Base):
    __tablename__ = "one_time_token"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)


class LoginAttempt(Base):
    __tablename__ = "login_attempt"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT
    )
    email_hash: Mapped[str] = mapped_column(String)
    ip: Mapped[str] = mapped_column(String)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)
    success: Mapped[bool] = mapped_column(Boolean)
