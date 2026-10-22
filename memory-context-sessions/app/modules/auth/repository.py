"""Data access for the authentication module."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class UserRepository:
    """Read and write user records."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The async database session.
        """
        self._session = session

    async def get_by_username(self, username: str) -> User | None:
        """Return the user with the given username, or None.

        Args:
            username: The username to look up.

        Returns:
            The user record, or None if not found.
        """
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Return the user with the given ID, or None.

        Args:
            user_id: The user's primary key.

        Returns:
            The user record, or None if not found.
        """
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persist a new user record.

        Args:
            user: The user entity to persist.

        Returns:
            The persisted user with its generated id.
        """
        self._session.add(user)
        return user
