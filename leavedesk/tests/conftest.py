"""Test harness.

Uses TEST_DATABASE_URL (a superuser/owner URL, e.g. the CI Postgres service) when set;
otherwise starts a throwaway local Postgres with pgserver. Migrations run as the owner;
the app under test runs `SET ROLE leavedesk_app`, so the restricted grants are real.
"""

import logging
import os
import secrets
import tempfile
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

logging.raiseExceptions = False  # pgserver logs to a closed stream at interpreter exit

APP_ROLE = "leavedesk_app"


def _owner_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    from pgserver import get_server  # type: ignore[attr-defined]

    server = get_server(tempfile.mkdtemp(prefix="leavedesk-pg-"))
    return server.get_uri().replace("postgresql://", "postgresql+psycopg://", 1)


OWNER_URL = _owner_url()
os.environ.update(
    ENVIRONMENT="test",
    DATABASE_URL=OWNER_URL,
    DATABASE_ROLE=APP_ROLE,
    MIGRATION_DATABASE_URL=OWNER_URL,
    EMAIL_BACKEND="mock",
)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine, text  # noqa: E402

from app.core.csrf import hash_token, new_token  # noqa: E402
from app.core.db import make_engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def owner_engine() -> Iterator[Engine]:
    engine = create_engine(OWNER_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config("alembic.ini"), "head")
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app_engine(owner_engine: Engine) -> Iterator[Engine]:
    """Connects like the app: as the restricted role."""
    engine = make_engine(OWNER_URL, APP_ROLE)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_db(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        conn.execute(text("TRUNCATE audit_log, session, team, employee CASCADE"))


@pytest.fixture
def app(owner_engine: Engine) -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@dataclass
class Login:
    employee_id: uuid.UUID
    token: str
    csrf: str

    @property
    def cookies(self) -> dict[str, str]:
        return {"session": self.token}

    @property
    def headers(self) -> dict[str, str]:
        return {"X-CSRF-Token": self.csrf}


@pytest.fixture
def make_login(owner_engine: Engine):  # type: ignore[no-untyped-def]
    def _make(
        role: str = "employee",
        *,
        active: bool = True,
        age: timedelta = timedelta(0),
        expires_in: timedelta = timedelta(hours=8),
    ) -> Login:
        eid = uuid.uuid4()
        token, csrf = new_token(), new_token()
        now = datetime.now(UTC)
        with owner_engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO employee (id, name, email, role, start_date, is_active) "
                    "VALUES (:id, 'Test', :email, :role, '2026-01-01', :active)"
                ),
                {
                    "id": eid,
                    "email": f"u{secrets.token_hex(4)}@asnet.com.vn",
                    "role": role,
                    "active": active,
                },
            )
            conn.execute(
                text(
                    "INSERT INTO session (employee_id, token_hash, csrf_token_hash, "
                    "created_at, last_seen_at, expires_at) "
                    "VALUES (:e, :t, :c, :created, :created, :exp)"
                ),
                {
                    "e": eid,
                    "t": hash_token(token),
                    "c": hash_token(csrf),
                    "created": now - age,
                    "exp": now + expires_in,
                },
            )
        return Login(eid, token, csrf)

    return _make
