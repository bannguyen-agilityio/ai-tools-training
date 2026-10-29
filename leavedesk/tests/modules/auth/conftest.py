import secrets
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.auth.passwords import hash_password

PASSWORD = "correct horse battery"


@dataclass
class User:
    id: uuid.UUID
    email: str
    password: str | None


MakeUser = Callable[..., Awaitable[User]]


@pytest.fixture
def make_user(owner_engine: AsyncEngine) -> MakeUser:
    async def _make(
        *, password: str | None = PASSWORD, active: bool = True, role: str = "employee"
    ) -> User:
        eid = uuid.uuid4()
        email = f"u{secrets.token_hex(4)}@asnet.com.vn"
        async with owner_engine.connect() as conn:
            await conn.execute(
                text(
                    "INSERT INTO employee (id, name, email, role, start_date, is_active) "
                    "VALUES (:id, 'Test User', :email, :role, '2026-01-01', :active)"
                ),
                {"id": eid, "email": email, "role": role, "active": active},
            )
            await conn.execute(
                text(
                    "INSERT INTO user_identity (employee_id, provider, password_hash) "
                    "VALUES (:e, 'password', :h)"
                ),
                {"e": eid, "h": hash_password(password) if password else None},
            )
        return User(eid, email, password)

    return _make
