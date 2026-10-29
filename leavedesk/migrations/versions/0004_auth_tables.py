"""user_identity, one_time_token, login_attempt with RLS and app-role grants (R1-R3, C-18)

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.core.config import get_settings

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

UUID_DEFAULT = sa.text("gen_random_uuid()")
NOW = sa.text("now()")
TABLES = ("user_identity", "one_time_token", "login_attempt")


def upgrade() -> None:
    app_role = get_settings().app_db_role
    if not app_role.isidentifier():
        raise ValueError("APP_DB_ROLE is not a valid role name")

    op.create_table(
        "user_identity",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column(
            "employee_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("employee.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String, nullable=False),
        # Null until the invite is accepted, and for provider 'google'.
        sa.Column("password_hash", sa.String),
        sa.Column("provider_subject", sa.String),
        sa.Column("password_changed_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.UniqueConstraint("employee_id", "provider", name="uq_user_identity_employee_provider"),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_user_identity_subject"),
        sa.CheckConstraint("provider IN ('password','google')", name="ck_user_identity_provider"),
        sa.CheckConstraint(
            "password_hash IS NULL OR password_hash LIKE '$argon2id$%'",
            name="ck_user_identity_argon2id",
        ),
    )

    op.create_table(
        "one_time_token",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column(
            "employee_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("employee.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String, nullable=False),
        sa.Column("token_hash", sa.String, nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.CheckConstraint("purpose IN ('invite','reset')", name="ck_one_time_token_purpose"),
    )
    op.create_index(
        "ix_one_time_token_employee_purpose", "one_time_token", ["employee_id", "purpose"]
    )

    op.create_table(
        "login_attempt",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("email_hash", sa.String, nullable=False),
        sa.Column("ip", sa.String, nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("success", sa.Boolean, nullable=False),
    )
    op.create_index("ix_login_attempt_email_at", "login_attempt", ["email_hash", "at"])
    op.create_index("ix_login_attempt_ip_at", "login_attempt", ["ip", "at"])

    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON user_identity TO {app_role}")
    # The purge job deletes used/expired tokens and old attempts.
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON one_time_token TO {app_role}")
    op.execute(f"GRANT SELECT, INSERT, DELETE ON login_attempt TO {app_role}")
    op.execute(f"REVOKE UPDATE, TRUNCATE ON login_attempt FROM {app_role}")
    op.execute(f"REVOKE TRUNCATE ON user_identity, one_time_token FROM {app_role}")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_table(table)
