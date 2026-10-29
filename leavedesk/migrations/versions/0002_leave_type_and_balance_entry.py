"""leave_type (seeded) and append-only balance_entry ledger (R5, R7, R8, R24, C-18)

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.core.config import get_settings

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

UUID_DEFAULT = sa.text("gen_random_uuid()")


def _app_role() -> str:
    role = get_settings().app_db_role
    if not role.isidentifier():
        raise ValueError("APP_DB_ROLE is not a valid role name")
    return role


def upgrade() -> None:
    app_role = _app_role()
    op.create_table(
        "leave_type",
        sa.Column("code", sa.String, primary_key=True),
        sa.Column("annual_allowance", sa.Numeric(4, 1)),
        sa.Column("carry_cap", sa.Numeric(4, 1), nullable=False),
        sa.Column("carries_over", sa.Boolean, nullable=False),
        sa.Column("is_limited", sa.Boolean, nullable=False),
        sa.Column("allow_backdate_days", sa.Integer, nullable=False),
        sa.Column("notice_exempt", sa.Boolean, nullable=False),
        sa.Column("is_sensitive", sa.Boolean, nullable=False),
        sa.CheckConstraint("code IN ('annual','sick','unpaid')", name="ck_leave_type_code"),
    )
    op.execute(
        "INSERT INTO leave_type (code, annual_allowance, carry_cap, carries_over, is_limited, "
        "allow_backdate_days, notice_exempt, is_sensitive) VALUES "
        "('annual', 12, 6, true, true, 0, false, false), "
        "('sick', 7, 0, false, true, 7, true, true), "
        "('unpaid', NULL, 0, false, false, 0, false, false)"
    )

    op.create_table(
        "balance_entry",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column(
            "employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id"), nullable=False
        ),
        sa.Column("leave_type_code", sa.String, sa.ForeignKey("leave_type.code"), nullable=False),
        sa.Column("leave_year", sa.Integer, nullable=False),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("days", sa.Numeric(4, 1), nullable=False),
        sa.Column("expires_on", sa.Date),
        sa.Column("reason", sa.String),
        sa.Column("source", sa.String, nullable=False, server_default="system"),
        sa.Column("idempotency_key", sa.String, unique=True),
        sa.Column("corrects_entry_id", pg.UUID(as_uuid=True), sa.ForeignKey("balance_entry.id")),
        sa.Column("created_by", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "kind IN ('opening','entitlement','prorata','carry_over','expiry','adjustment')",
            name="ck_balance_entry_kind",
        ),
        sa.CheckConstraint("source IN ('manual','system')", name="ck_balance_entry_source"),
        sa.CheckConstraint("leave_type_code <> 'unpaid'", name="ck_balance_entry_not_unpaid"),
        sa.CheckConstraint("days = round(days * 2) / 2", name="ck_balance_entry_half_steps"),
        sa.CheckConstraint(
            "kind <> 'adjustment' OR (reason IS NOT NULL AND length(btrim(reason)) > 0)",
            name="ck_balance_entry_adjustment_reason",
        ),
        sa.CheckConstraint(
            "kind NOT IN ('opening','carry_over') OR source <> 'manual' OR days BETWEEN 0 AND 40",
            name="ck_balance_entry_manual_range",
        ),
        sa.CheckConstraint(
            "(kind = 'carry_over') = (expires_on IS NOT NULL)", name="ck_balance_entry_expires_on"
        ),
    )
    op.create_index(
        "ix_balance_entry_employee_year", "balance_entry", ["employee_id", "leave_year"]
    )

    for table in ("leave_type", "balance_entry"):
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(f"GRANT SELECT ON leave_type TO {app_role}")
    # Append-only (R24): no UPDATE, DELETE or TRUNCATE.
    op.execute(f"GRANT SELECT, INSERT ON balance_entry TO {app_role}")
    op.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON balance_entry FROM {app_role}")


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "balance_entry" CASCADE')
    op.execute('DROP TABLE IF EXISTS "leave_type" CASCADE')
