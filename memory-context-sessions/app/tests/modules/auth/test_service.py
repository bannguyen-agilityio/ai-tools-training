"""Tests for the authentication service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService


class TestAuthService:
    """Tests for AuthService business logic."""

    def _make_service(self, session: AsyncSession) -> AuthService:
        """Build a service backed by the given session."""
        return AuthService(UserRepository(session))

    async def test_register_success(self, db_session: AsyncSession) -> None:
        """Registering a new user returns the persisted record."""
        service = self._make_service(db_session)
        user = await service.register("newuser", "securepass", "New User")
        assert user.username == "newuser"
        assert user.full_name == "New User"
        assert user.id is not None

    async def test_register_duplicate_username(self, db_session: AsyncSession) -> None:
        """Duplicate username raises ConflictError."""
        service = self._make_service(db_session)
        with pytest.raises(ConflictError) as exc_info:
            await service.register("admin", "securepass", "Another Admin")
        assert exc_info.value.code == "USERNAME_ALREADY_EXISTS"

    async def test_register_then_authenticate(self, db_session: AsyncSession) -> None:
        """A newly registered user can authenticate."""
        service = self._make_service(db_session)
        await service.register("alice", "strongpass", "Alice A")
        token = await service.authenticate("alice", "strongpass")
        assert len(token) > 0

    async def test_authenticate_valid(self, db_session: AsyncSession) -> None:
        """Valid credentials return a token."""
        service = self._make_service(db_session)
        token = await service.authenticate("admin", "admin123")
        assert len(token) > 0

    async def test_authenticate_wrong_password(self, db_session: AsyncSession) -> None:
        """Wrong password raises AuthenticationError with INVALID_CREDENTIALS."""
        service = self._make_service(db_session)
        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate("admin", "wrong")
        assert exc_info.value.code == "INVALID_CREDENTIALS"
        assert exc_info.value.message == "Incorrect username or password"

    async def test_authenticate_unknown_user(self, db_session: AsyncSession) -> None:
        """Unknown user raises AuthenticationError with INVALID_CREDENTIALS."""
        service = self._make_service(db_session)
        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate("nobody", "admin123")
        assert exc_info.value.code == "INVALID_CREDENTIALS"

    async def test_resolve_token(self, db_session: AsyncSession) -> None:
        """A valid token resolves to its username."""
        service = self._make_service(db_session)
        token = await service.authenticate("admin", "admin123")
        assert service.resolve_token(token) == "admin"

    async def test_resolve_invalid_token(self, db_session: AsyncSession) -> None:
        """An invalid token raises AuthenticationError with INVALID_TOKEN."""
        service = self._make_service(db_session)
        with pytest.raises(AuthenticationError) as exc_info:
            service.resolve_token("bad-token")
        assert exc_info.value.code == "INVALID_TOKEN"

    async def test_get_user(self, db_session: AsyncSession) -> None:
        """Existing user returns their data."""
        service = self._make_service(db_session)
        user = await service.get_user("admin")
        assert user is not None
        assert user.full_name == "Admin User"

    async def test_get_user_not_found(self, db_session: AsyncSession) -> None:
        """Non-existent user returns None."""
        service = self._make_service(db_session)
        assert await service.get_user("nobody") is None
