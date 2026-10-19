"""Shared test fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("APP_DATABASE_URL", "sqlite+aiosqlite://")

from app.core.security import generate_salt, hash_password
from app.infrastructure.database import Base, get_db_session
from app.main import app
from app.modules.auth.models import User

_test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_db_session() -> AsyncGenerator[AsyncSession]:
    """Provide a test database session."""
    async with _test_session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
async def _setup_test_db() -> AsyncGenerator[None]:
    """Create tables, seed admin user, and clean up after each test."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _test_session_factory() as session:
        salt = generate_salt()
        session.add(
            User(
                username="admin",
                password_hash=hash_password("admin123", salt),
                salt=salt,
                full_name="Admin User",
            )
        )
        await session.commit()

    app.dependency_overrides[get_db_session] = _override_get_db_session
    yield
    app.dependency_overrides.clear()

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client() -> TestClient:
    """Provide a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def auth_token(client: TestClient) -> str:
    """Authenticate as admin and return a valid access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Return authorization headers with a valid bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Provide a test database session for service-level tests."""
    async with _test_session_factory() as session:
        yield session
