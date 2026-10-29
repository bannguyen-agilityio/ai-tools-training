import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LeaveType(Base):
    __tablename__ = "leave_type"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    annual_allowance: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    carry_cap: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    carries_over: Mapped[bool] = mapped_column(Boolean)
    is_limited: Mapped[bool] = mapped_column(Boolean)
    allow_backdate_days: Mapped[int] = mapped_column(Integer)
    notice_exempt: Mapped[bool] = mapped_column(Boolean)
    is_sensitive: Mapped[bool] = mapped_column(Boolean)


class BalanceEntry(Base):
    """Append-only ledger: the app role has INSERT and SELECT only (R24)."""

    __tablename__ = "balance_entry"
    __table_args__ = (Index("ix_balance_entry_employee_year", "employee_id", "leave_year"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employee.id"))
    leave_type_code: Mapped[str] = mapped_column(ForeignKey("leave_type.code"))
    leave_year: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String)
    days: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    expires_on: Mapped[date | None] = mapped_column(Date)
    reason: Mapped[str | None] = mapped_column(String)
    source: Mapped[str] = mapped_column(String, server_default="system")
    idempotency_key: Mapped[str | None] = mapped_column(String, unique=True)
    corrects_entry_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("balance_entry.id"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
