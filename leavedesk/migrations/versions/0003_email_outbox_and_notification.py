"""email_outbox and notification with RLS and app-role grants (R26, R35)

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.core.config import get_settings

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

UUID_DEFAULT = sa.text("gen_random_uuid()")
NOW = sa.text("now()")


def upgrade() -> None:
    app_role = get_settings().app_db_role
    if not app_role.isidentifier():
        raise ValueError("APP_DB_ROLE is not a valid role name")

    op.create_table(
        "email_outbox",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("recipient_employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employee.id")),
        sa.Column("to_address", sa.String, nullable=False),
        sa.Column("template", sa.String, nullable=False),
        sa.Column("payload", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("subject", sa.String, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("dedupe_key", sa.String, nullable=False, unique=True),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_try_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.String),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.CheckConstraint(
            "status IN ('pending','sent','failed','mocked')", name="ck_email_outbox_status"
        ),
    )
    op.create_index("ix_email_outbox_status_next_try", "email_outbox", ["status", "next_try_at"])

    op.create_table(
        "notification",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column(
            "employee_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("employee.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("body", sa.String, nullable=False),
        sa.Column("link", sa.String, nullable=False),
        sa.Column("request_id", pg.UUID(as_uuid=True)),
        sa.Column("dedupe_key", sa.String, nullable=False, unique=True),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_index(
        "ix_notification_employee_read_created",
        "notification",
        ["employee_id", "read_at", "created_at"],
    )

    for table in ("email_outbox", "notification"):
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        # No DELETE or TRUNCATE: rows are kept; status and read_at are the only updates.
        op.execute(f'GRANT SELECT, INSERT, UPDATE ON "{table}" TO {app_role}')
        op.execute(f'REVOKE DELETE, TRUNCATE ON "{table}" FROM {app_role}')


def downgrade() -> None:
    for table in ("notification", "email_outbox"):
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
