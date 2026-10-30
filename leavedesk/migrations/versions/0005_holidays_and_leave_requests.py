"""public_holiday (seeded), leave_request and leave_request_day (R6, R11, C-8, C-18)

The request tables are created here without request endpoints (plan 10 owns those) so the
holiday impact query and the day expansion are testable now.

Revision ID: 0005
Revises: 0004
"""

from datetime import date

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.core.config import get_settings

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

UUID_DEFAULT = sa.text("gen_random_uuid()")
NOW = sa.text("now()")
TABLES = ("public_holiday", "leave_request", "leave_request_day")

# Spec Appendix A (A-19). Taken from press reports of the Ministry of Home Affairs notices and
# the Culture Day resolution; the decree texts themselves are not yet checked.
TET = "Tet (Lunar New Year)"
SEED = (
    ("2026-01-01", "New Year's Day"),
    ("2026-01-02", "New Year holiday (extra day)"),
    ("2026-02-16", TET),
    ("2026-02-17", TET),
    ("2026-02-18", TET),
    ("2026-02-19", TET),
    ("2026-02-20", TET),
    ("2026-04-27", "Hung Kings' Commemoration (compensatory day)"),
    ("2026-04-30", "Reunification Day"),
    ("2026-05-01", "International Labour Day"),
    ("2026-08-31", "National Day holiday (extra day)"),
    ("2026-09-01", "National Day"),
    ("2026-09-02", "National Day"),
    ("2026-11-24", "Vietnam Culture Day"),
    ("2027-01-01", "New Year's Day"),
    ("2027-02-04", TET),
    ("2027-02-05", TET),
    ("2027-02-08", TET),
    ("2027-02-09", TET),
    ("2027-02-10", TET),
    ("2027-04-16", "Hung Kings' Commemoration"),
    ("2027-04-30", "Reunification Day"),
    ("2027-05-03", "International Labour Day (compensatory day)"),
    ("2027-09-02", "National Day"),
    ("2027-09-03", "National Day holiday (extra day)"),
    ("2027-11-24", "Vietnam Culture Day"),
)


def upgrade() -> None:
    app_role = get_settings().app_db_role
    if not app_role.isidentifier():
        raise ValueError("APP_DB_ROLE is not a valid role name")

    op.create_table(
        "public_holiday",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("holiday_date", sa.Date, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("created_by", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.CheckConstraint("source IN ('seed','manual')", name="ck_public_holiday_source"),
        sa.CheckConstraint("length(btrim(name)) BETWEEN 1 AND 100", name="ck_public_holiday_name"),
    )
    holiday = sa.table(
        "public_holiday", sa.column("holiday_date", sa.Date), sa.column("name"), sa.column("source")
    )
    op.bulk_insert(
        holiday,
        [{"holiday_date": date.fromisoformat(d), "name": n, "source": "seed"} for d, n in SEED],
    )

    op.create_table(
        "leave_request",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column(
            "employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id"), nullable=False
        ),
        sa.Column("leave_type_code", sa.String, sa.ForeignKey("leave_type.code"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("start_part", sa.String, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("end_part", sa.String, nullable=False),
        sa.Column("working_days", sa.Numeric(4, 1), nullable=False),  # snapshot (C-8)
        sa.Column("note", sa.String),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("queue", sa.String, nullable=False),
        sa.Column("assigned_to", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("notice_warning", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("entered_by", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("entry_reason", sa.String),
        sa.Column("decided_by", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("decided_on_behalf_of", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decision_reason", sa.String),
        sa.Column("cancelled_by", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("cancel_reason", sa.String),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.CheckConstraint("end_date >= start_date", name="ck_leave_request_dates"),
        sa.CheckConstraint(
            "start_part IN ('full','am','pm') AND end_part IN ('full','am','pm')",
            name="ck_leave_request_parts_values",
        ),
        sa.CheckConstraint(
            "(start_date = end_date AND start_part = end_part)"
            " OR (start_date < end_date AND start_part IN ('full','pm')"
            " AND end_part IN ('full','am'))",
            name="ck_leave_request_parts",
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','cancelled')",
            name="ck_leave_request_status",
        ),
        sa.CheckConstraint("queue IN ('manager','hr','deputy')", name="ck_leave_request_queue"),
        sa.CheckConstraint("working_days > 0", name="ck_leave_request_working_days"),
        sa.CheckConstraint(
            "working_days = round(working_days * 2) / 2", name="ck_leave_request_half_steps"
        ),
        sa.CheckConstraint(
            "note IS NULL OR length(note) <= 500", name="ck_leave_request_note_length"
        ),
        sa.CheckConstraint(
            "status <> 'rejected' OR (decision_reason IS NOT NULL"
            " AND length(btrim(decision_reason)) BETWEEN 1 AND 500)",
            name="ck_leave_request_rejection_reason",
        ),
        sa.CheckConstraint(
            "NOT (status = 'cancelled' AND cancelled_by <> employee_id)"
            " OR cancel_reason IS NOT NULL",
            name="ck_leave_request_cancel_reason",
        ),
        sa.CheckConstraint(
            "decided_by <> employee_id AND decided_on_behalf_of <> employee_id",
            name="ck_leave_request_no_self_approval",
        ),
    )
    op.create_index("ix_leave_request_assigned_status", "leave_request", ["assigned_to", "status"])
    op.create_index("ix_leave_request_queue_status", "leave_request", ["queue", "status"])
    op.create_index(
        "ix_leave_request_employee_start", "leave_request", ["employee_id", "start_date"]
    )
    op.create_index("ix_leave_request_status_start", "leave_request", ["status", "start_date"])

    op.create_table(
        "leave_request_day",
        sa.Column(
            "request_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("leave_request.id"),
            primary_key=True,
        ),
        sa.Column("leave_date", sa.Date, primary_key=True),
        sa.Column("slot", sa.String, primary_key=True),
        sa.Column(
            "employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id"), nullable=False
        ),
        sa.Column("leave_year", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.CheckConstraint("slot IN ('am','pm')", name="ck_leave_request_day_slot"),
        sa.CheckConstraint(
            "leave_year = EXTRACT(YEAR FROM leave_date)", name="ck_leave_request_day_year"
        ),
        sa.CheckConstraint(
            "EXTRACT(ISODOW FROM leave_date) < 6", name="ck_leave_request_day_weekday"
        ),
    )
    # Overlap is impossible even under concurrent submits (R13); am + pm on one date do not clash.
    op.create_index(
        "uq_leave_request_day_active",
        "leave_request_day",
        ["employee_id", "leave_date", "slot"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.create_index(
        "ix_leave_request_day_date_employee",
        "leave_request_day",
        ["leave_date", "employee_id"],
        postgresql_where=sa.text("is_active"),
    )
    op.create_index(
        "ix_leave_request_day_employee_year", "leave_request_day", ["employee_id", "leave_year"]
    )

    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON public_holiday TO {app_role}")
    # Requests are never deleted: they are cancelled (R16, R21).
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON leave_request, leave_request_day TO {app_role}")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
