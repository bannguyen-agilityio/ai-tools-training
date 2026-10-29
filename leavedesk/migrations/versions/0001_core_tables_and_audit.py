"""employee, team, session, audit_log with RLS and app-role grants (R29, R30, C-18)

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.core.config import get_settings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLES = ("team", "employee", "session", "audit_log")
UUID_DEFAULT = sa.text("gen_random_uuid()")
NOW = sa.text("now()")


def _ts(name: str, **kw) -> sa.Column:  # type: ignore[no-untyped-def]
    return sa.Column(name, sa.DateTime(timezone=True), server_default=NOW, **kw)


def _app_role() -> str:
    # Read lazily: importing this module (e.g. to list heads) must not need app settings.
    role = get_settings().app_db_role
    if not role.isidentifier():
        raise ValueError("APP_DB_ROLE is not a valid role name")
    return role


def upgrade() -> None:
    app_role = _app_role()
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "team",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("manager_id", pg.UUID(as_uuid=True)),
        _ts("created_at", nullable=False),
        _ts("updated_at", nullable=False),
    )
    op.create_table(
        "employee",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("email", pg.CITEXT, nullable=False, unique=True),
        sa.Column("role", sa.String, nullable=False, server_default="employee"),
        sa.Column("is_hr_deputy", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("team_id", pg.UUID(as_uuid=True), sa.ForeignKey("team.id")),
        sa.Column("manager_id", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("deactivated_at", sa.DateTime(timezone=True)),
        _ts("created_at", nullable=False),
        _ts("updated_at", nullable=False),
        sa.CheckConstraint("email LIKE '%@asnet.com.vn'", name="ck_employee_email_domain"),
        sa.CheckConstraint("role IN ('employee','manager','hr')", name="ck_employee_role"),
        sa.CheckConstraint("manager_id <> id", name="ck_employee_not_own_manager"),
        sa.CheckConstraint("NOT (is_hr_deputy AND role = 'hr')", name="ck_employee_deputy_not_hr"),
    )
    op.create_foreign_key("fk_team_manager", "team", "employee", ["manager_id"], ["id"])
    op.create_index(
        "uq_employee_one_active_deputy",
        "employee",
        ["is_hr_deputy"],
        unique=True,
        postgresql_where=sa.text("is_hr_deputy AND is_active"),
    )
    op.create_table(
        "session",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column(
            "employee_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("employee.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String, nullable=False, unique=True),
        sa.Column("csrf_token_hash", sa.String, nullable=False),
        _ts("created_at", nullable=False),
        _ts("last_seen_at", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("actor_id", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("acting_for_id", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("target_type", sa.String, nullable=False),
        sa.Column("target_id", sa.String),
        sa.Column("detail", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ip", sa.String),
        _ts("at", nullable=False),
    )
    op.create_index("ix_audit_log_at", "audit_log", ["at"])
    op.create_index("ix_audit_log_target", "audit_log", ["target_type", "target_id"])
    op.create_index("ix_audit_log_actor_at", "audit_log", ["actor_id", "at"])

    # C-18: RLS on, no policies. Only roles that bypass RLS (the app role) can read.
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')

    # `anon` exists on Supabase; create it elsewhere so grants/tests behave the same.
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') "
        "THEN CREATE ROLE anon NOLOGIN; END IF; END $$"
    )
    # The app role bypasses RLS (there are no policies) but is NOT the table owner,
    # so the grants below are what restrict it. Needs a role allowed to set BYPASSRLS.
    op.execute(
        f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{app_role}') "
        f"THEN CREATE ROLE {app_role} NOLOGIN BYPASSRLS; END IF; END $$"
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {app_role}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON team, employee, session TO {app_role}")
    # Append-only (R30): no UPDATE, DELETE or TRUNCATE.
    op.execute(f"GRANT SELECT, INSERT ON audit_log TO {app_role}")
    op.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM {app_role}")


def downgrade() -> None:
    for table in ("audit_log", "session", "employee", "team"):
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {_app_role()}")
