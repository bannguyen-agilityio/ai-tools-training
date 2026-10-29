"""Test harness.

Configuration is read like production: from environment variables and an env file
(tests/test.env, chosen via ENV_FILE). The database URL comes from TEST_DATABASE_URL
(an owner/superuser URL, e.g. the CI Postgres service or a local Docker Postgres).
Migrations run as the owner; the app under test
connects with `-c role=<APP_DB_ROLE>`, so the restricted grants are real.
"""

import asyncio
import os
import secrets
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import pytest

os.environ.setdefault("ENV_FILE", str(Path(__file__).parent / "test.env"))


def _owner_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.exit(
            "TEST_DATABASE_URL is not set; see docs/runbooks/secrets.md section 4.",
            returncode=2,
        )
    return url


OWNER_URL = _owner_url()
os.environ["DATABASE_URL"] = OWNER_URL
os.environ["MIGRATION_DATABASE_URL"] = OWNER_URL

import httpx  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi import Depends, FastAPI  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.csrf import hash_token, new_token  # noqa: E402
from app.core.db import get_db, make_engine  # noqa: E402
from app.core.schemas import StrictModel  # noqa: E402
from app.main import create_app  # noqa: E402
from app.modules.identity.dependencies import get_current_user  # noqa: E402
from app.modules.identity.models import Employee  # noqa: E402


async def _reset_schema() -> None:
    engine = create_async_engine(OWNER_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with engine.connect() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    asyncio.run(_reset_schema())
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def app_role() -> str:
    return get_settings().app_db_role


@pytest.fixture
async def owner_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(OWNER_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def app_engine() -> AsyncIterator[AsyncEngine]:
    """Connects like the app: as the restricted role."""
    engine = make_engine(OWNER_URL, set_role=True, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_db(owner_engine: AsyncEngine) -> None:
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("TRUNCATE email_outbox, notification, audit_log, session, team, employee CASCADE")
        )


@pytest.fixture
def app(app_engine: AsyncEngine) -> FastAPI:
    app = create_app()
    factory = async_sessionmaker(app_engine, expire_on_commit=False)

    async def _db() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@dataclass
class Login:
    employee_id: uuid.UUID
    token: str
    csrf: str

    @property
    def headers(self) -> dict[str, str]:
        """Session cookie only: enough for safe (GET) calls."""
        return {"Cookie": f"session={self.token}"}

    @property
    def mutating_headers(self) -> dict[str, str]:
        """Session cookie plus CSRF token: for state-changing calls."""
        return {**self.headers, "X-CSRF-Token": self.csrf}


MakeLogin = Callable[..., Awaitable[Login]]


@pytest.fixture
def make_login(owner_engine: AsyncEngine) -> MakeLogin:
    async def _make(
        role: str = "employee",
        *,
        active: bool = True,
        age: timedelta = timedelta(0),
        expires_in: timedelta = timedelta(hours=8),
    ) -> Login:
        eid = uuid.uuid4()
        token, csrf = new_token(), new_token()
        now = datetime.now(UTC)
        async with owner_engine.connect() as conn:
            await conn.execute(
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
            await conn.execute(
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


class Probe(StrictModel):
    name: str


@pytest.fixture
def probe_app(app: FastAPI) -> FastAPI:
    """Adds throwaway routes that exercise the baseline (CSRF, strict body, 500)."""

    @app.post("/api/v1/_probe")
    async def probe(
        body: Probe, user: Annotated[Employee, Depends(get_current_user)]
    ) -> dict[str, str]:
        return {"name": body.name}

    @app.get("/api/v1/_boom")
    async def boom(user: Annotated[Employee, Depends(get_current_user)]) -> None:
        raise RuntimeError("secret-internal-detail")

    return app


@pytest.fixture
async def pclient(probe_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=probe_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
