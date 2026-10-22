"""Tests for the authentication repository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository


class TestUserRepository:
    """Tests for UserRepository persistence behaviour."""

    async def test_create_assigns_id(self, db_session: AsyncSession) -> None:
        """create() flushes so the generated id is available immediately."""
        repo = UserRepository(db_session)
        user = await repo.create(
            User(username="flushed", password_hash="h", salt="s", full_name="Flushed")
        )
        assert user.id is not None

    async def test_create_duplicate_raises_conflict(
        self, db_session: AsyncSession
    ) -> None:
        """A unique-constraint violation becomes a ConflictError."""
        repo = UserRepository(db_session)
        duplicate = User(
            username=settings.seed_username,
            password_hash="h",
            salt="s",
            full_name="Dup",
        )
        with pytest.raises(ConflictError) as exc_info:
            await repo.create(duplicate)
        assert exc_info.value.code == "USERNAME_ALREADY_EXISTS"
