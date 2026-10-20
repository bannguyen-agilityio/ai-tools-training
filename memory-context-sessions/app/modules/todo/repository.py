"""Data access for the todo module."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.todo.models import Todo


class TodoRepository:
    """Read and write todo records."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The async database session.
        """
        self._session = session

    async def list_by_user(
        self, user_id: int, *, offset: int = 0, limit: int = 10
    ) -> list[Todo]:
        """Return a page of todos for the given user.

        Args:
            user_id: The owner's user ID.
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            A list of todo records ordered by creation time descending.
        """
        result = await self._session.execute(
            select(Todo)
            .where(Todo.user_id == user_id)
            .order_by(Todo.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        """Return the total number of todos for the given user.

        Args:
            user_id: The owner's user ID.

        Returns:
            The count of matching records.
        """
        result = await self._session.execute(
            select(func.count()).select_from(Todo).where(Todo.user_id == user_id)
        )
        return result.scalar_one()

    async def get_by_id_and_user(self, todo_id: int, user_id: int) -> Todo | None:
        """Return a single todo owned by the given user.

        Args:
            todo_id: The todo's primary key.
            user_id: The owner's user ID.

        Returns:
            The todo record, or ``None`` if not found.
        """
        result = await self._session.execute(
            select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, todo: Todo) -> Todo:
        """Persist a new todo record.

        Args:
            todo: The todo entity to persist.

        Returns:
            The persisted todo with its generated id.
        """
        self._session.add(todo)
        await self._session.flush()
        return todo

    async def flush(self) -> None:
        """Flush pending changes to the database."""
        await self._session.flush()
