"""Business logic for todos."""

from app.core.exceptions import NotFoundError
from app.modules.auth.repository import UserRepository
from app.modules.todo.models import Todo
from app.modules.todo.repository import TodoRepository


class TodoService:
    """Handle todo use cases."""

    def __init__(
        self,
        todo_repo: TodoRepository,
        user_repo: UserRepository | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            todo_repo: The todo data-access repository.
            user_repo: The user data-access repository (needed for move).
        """
        self._todo_repo = todo_repo
        self._user_repo = user_repo

    async def list_todos(
        self, user_id: int, *, offset: int = 0, limit: int = 10
    ) -> tuple[list[Todo], int]:
        """Return a page of todos for a user.

        Args:
            user_id: The owner's user ID.
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            A tuple of (items, total_count).
        """
        items = await self._todo_repo.list_by_user(user_id, offset=offset, limit=limit)
        total = await self._todo_repo.count_by_user(user_id)
        return items, total

    async def get_todo(self, todo_id: int, user_id: int) -> Todo:
        """Return a single todo owned by the user.

        Args:
            todo_id: The todo's primary key.
            user_id: The owner's user ID.

        Returns:
            The todo record.

        Raises:
            NotFoundError: If the todo does not exist or is not owned by the user.
        """
        todo = await self._todo_repo.get_by_id_and_user(todo_id, user_id)
        if not todo:
            raise NotFoundError(message="Todo not found", code="TODO_NOT_FOUND")
        return todo

    async def create_todo(
        self, user_id: int, title: str, description: str | None
    ) -> Todo:
        """Create a new todo for a user.

        Args:
            user_id: The owner's user ID.
            title: The todo title.
            description: Optional description.

        Returns:
            The newly created todo.
        """
        todo = Todo(title=title, description=description, user_id=user_id)
        return await self._todo_repo.create(todo)

    async def delete_todo(self, todo_id: int, user_id: int) -> None:
        """Delete a todo owned by the user.

        Args:
            todo_id: The todo's primary key.
            user_id: The owner's user ID.

        Raises:
            NotFoundError: If the todo does not exist or is not owned by the user.
        """
        todo = await self._todo_repo.get_by_id_and_user(todo_id, user_id)
        if not todo:
            raise NotFoundError(message="Todo not found", code="TODO_NOT_FOUND")
        await self._todo_repo.delete(todo)

    async def copy_todo(self, todo_id: int, user_id: int) -> Todo:
        """Create a copy of an existing todo.

        Args:
            todo_id: The source todo's primary key.
            user_id: The owner's user ID.

        Returns:
            The newly created copy.

        Raises:
            NotFoundError: If the source todo does not exist or is not owned by the user.
        """
        source = await self.get_todo(todo_id, user_id)
        return await self.create_todo(user_id, source.title, source.description)

    async def bulk_delete_todos(self, todo_ids: list[int], user_id: int) -> int:
        """Delete multiple todos owned by the user.

        Args:
            todo_ids: The primary keys of the todos to delete.
            user_id: The owner's user ID.

        Returns:
            The number of todos actually deleted.
        """
        return await self._todo_repo.delete_many_by_ids_and_user(todo_ids, user_id)

    async def move_todo(self, todo_id: int, user_id: int, target_user_id: int) -> Todo:
        """Move a todo to a different user.

        Args:
            todo_id: The todo's primary key.
            user_id: The current owner's user ID.
            target_user_id: The new owner's user ID.

        Returns:
            The moved todo with updated ownership.

        Raises:
            NotFoundError: If the todo or target user does not exist.
        """
        todo = await self._todo_repo.get_by_id_and_user(todo_id, user_id)
        if not todo:
            raise NotFoundError(message="Todo not found", code="TODO_NOT_FOUND")
        if self._user_repo is None:
            raise RuntimeError("UserRepository is required for move_todo")
        target_user = await self._user_repo.get_by_id(target_user_id)
        if not target_user:
            raise NotFoundError(
                message="Target user not found", code="TARGET_USER_NOT_FOUND"
            )
        return await self._todo_repo.update_user(todo, target_user_id)

    async def update_todo(
        self,
        todo_id: int,
        user_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        completed: bool | None = None,
    ) -> Todo:
        """Update an existing todo.

        Args:
            todo_id: The todo's primary key.
            user_id: The owner's user ID.
            title: New title, or ``None`` to keep the current value.
            description: New description, or ``None`` to keep the current value.
            completed: New completed status, or ``None`` to keep the current value.

        Returns:
            The updated todo.

        Raises:
            NotFoundError: If the todo does not exist or is not owned by the user.
        """
        todo = await self._todo_repo.get_by_id_and_user(todo_id, user_id)
        if not todo:
            raise NotFoundError(message="Todo not found", code="TODO_NOT_FOUND")
        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if completed is not None:
            todo.completed = completed
        await self._todo_repo.flush()
        return todo
