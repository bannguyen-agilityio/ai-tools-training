import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

UUID_DEFAULT = text("gen_random_uuid()")
NOW = text("now()")


class Team(Base):
    __tablename__ = "team"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT
    )
    name: Mapped[str] = mapped_column(String, unique=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employee.id", use_alter=True, name="fk_team_manager")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)


class Employee(Base):
    __tablename__ = "employee"
    __table_args__ = (
        CheckConstraint("email LIKE '%@asnet.com.vn'", name="ck_employee_email_domain"),
        CheckConstraint("role IN ('employee','manager','hr')", name="ck_employee_role"),
        CheckConstraint("manager_id <> id", name="ck_employee_not_own_manager"),
        CheckConstraint("NOT (is_hr_deputy AND role = 'hr')", name="ck_employee_deputy_not_hr"),
        Index(
            "uq_employee_one_active_deputy",
            "is_hr_deputy",
            unique=True,
            postgresql_where=text("is_hr_deputy AND is_active"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT
    )
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    role: Mapped[str] = mapped_column(String, server_default="employee")
    is_hr_deputy: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("team.id"))
    manager_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("employee.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)


class Session(Base):
    __tablename__ = "session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    csrf_token_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
