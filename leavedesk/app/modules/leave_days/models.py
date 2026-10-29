import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LeaveRequest(Base):
    """Request header. Endpoints arrive with plan 10; the table exists now for R11 impact."""

    __tablename__ = "leave_request"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employee.id"))
    leave_type_code: Mapped[str] = mapped_column(ForeignKey("leave_type.code"))
    start_date: Mapped[date] = mapped_column(Date)
    start_part: Mapped[str] = mapped_column(String)
    end_date: Mapped[date] = mapped_column(Date)
    end_part: Mapped[str] = mapped_column(String)
    working_days: Mapped[Decimal] = mapped_column(Numeric(4, 1))  # snapshot, never rewritten (C-8)
    note: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, server_default="pending")
    queue: Mapped[str] = mapped_column(String)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    notice_warning: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    entered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    entry_reason: Mapped[str | None] = mapped_column(String)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    decided_on_behalf_of: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(String)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class LeaveRequestDay(Base):
    """One row per working half day; weekends and holidays are never stored (spec 5.1)."""

    __tablename__ = "leave_request_day"
    __table_args__ = (
        Index(
            "uq_leave_request_day_active",
            "employee_id",
            "leave_date",
            "slot",
            unique=True,
            postgresql_where=text("is_active"),
        ),
        Index(
            "ix_leave_request_day_date_employee",
            "leave_date",
            "employee_id",
            postgresql_where=text("is_active"),
        ),
        Index("ix_leave_request_day_employee_year", "employee_id", "leave_year"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leave_request.id"), primary_key=True)
    leave_date: Mapped[date] = mapped_column(Date, primary_key=True)
    slot: Mapped[str] = mapped_column(String, primary_key=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employee.id"))
    leave_year: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
