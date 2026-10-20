"""Data access for the todo module."""

from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select
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
            .order_by(Todo.created_at.desc(), Todo.id.desc())
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

    async def delete(self, todo: Todo) -> None:
        """Remove a todo record from the database.

        Args:
            todo: The todo entity to delete.
        """
        await self._session.delete(todo)
        await self._session.flush()

    async def delete_many_by_ids_and_user(
        self, todo_ids: list[int], user_id: int
    ) -> int:
        """Delete todos matching the given IDs and user.

        Args:
            todo_ids: The primary keys of the todos to delete.
            user_id: The owner's user ID.

        Returns:
            The number of rows actually deleted.
        """
        result = cast(
            "CursorResult[Any]",
            await self._session.execute(
                delete(Todo).where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
            ),
        )
        await self._session.flush()
        return result.rowcount

    async def update_user(self, todo: Todo, new_user_id: int) -> Todo:
        """Change the owner of a todo record.

        Args:
            todo: The todo entity to reassign.
            new_user_id: The new owner's user ID.

        Returns:
            The updated todo.
        """
        todo.user_id = new_user_id
        await self._session.flush()
        return todo

    async def flush(self) -> None:
        """Flush pending changes to the database."""
        await self._session.flush()
