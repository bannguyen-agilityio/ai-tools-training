"""Tests for the todo service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.modules.auth.repository import UserRepository
from app.modules.todo.repository import TodoRepository
from app.modules.todo.service import TodoService


class TestTodoService:
    """Tests for TodoService business logic."""

    def _make_service(self, session: AsyncSession) -> TodoService:
        """Build a service backed by the given session."""
        return TodoService(TodoRepository(session))

    async def _get_seed_user_id(self, session: AsyncSession) -> int:
        """Look up the seed user's ID."""
        user_repo = UserRepository(session)
        user = await user_repo.get_by_username(settings.seed_username)
        assert user is not None
        return user.id

    async def test_list_empty(self, db_session: AsyncSession) -> None:
        """User with no todos gets an empty list and zero count."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)
        items, total = await service.list_todos(user_id)
        assert items == []
        assert total == 0

    async def test_create_and_list(self, db_session: AsyncSession) -> None:
        """Created todos appear in the user's list."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)

        await service.create_todo(user_id, "First", None)
        await service.create_todo(user_id, "Second", "Details")

        items, total = await service.list_todos(user_id)
        assert len(items) == 2
        assert total == 2
        titles = {t.title for t in items}
        assert titles == {"First", "Second"}

    async def test_create_returns_todo(self, db_session: AsyncSession) -> None:
        """create_todo returns the persisted record with an id."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)

        todo = await service.create_todo(user_id, "Test", "A description")
        assert todo.id is not None
        assert todo.title == "Test"
        assert todo.description == "A description"
        assert todo.completed is False
        assert todo.user_id == user_id

    async def test_list_only_own_todos(self, db_session: AsyncSession) -> None:
        """Todos from other users are not included."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)

        await service.create_todo(user_id, "Mine", None)
        await service.create_todo(9999, "Not mine", None)

        items, total = await service.list_todos(user_id)
        assert len(items) == 1
        assert total == 1
        assert items[0].title == "Mine"

    async def test_get_todo(self, db_session: AsyncSession) -> None:
        """get_todo returns the todo detail."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)
        created = await service.create_todo(user_id, "Fetch me", "Details here")

        todo = await service.get_todo(created.id, user_id)
        assert todo.id == created.id
        assert todo.title == "Fetch me"
        assert todo.description == "Details here"

    async def test_get_todo_not_found(self, db_session: AsyncSession) -> None:
        """get_todo raises NotFoundError for a nonexistent todo."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)

        with pytest.raises(NotFoundError):
            await service.get_todo(9999, user_id)

    async def test_get_todo_other_user(self, db_session: AsyncSession) -> None:
        """get_todo raises NotFoundError when the todo belongs to another user."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)
        todo = await service.create_todo(user_id, "Private", None)

        with pytest.raises(NotFoundError):
            await service.get_todo(todo.id, 9999)

    async def test_list_with_pagination(self, db_session: AsyncSession) -> None:
        """Offset and limit control which items are returned."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)

        for i in range(5):
            await service.create_todo(user_id, f"Todo {i}", None)

        items, total = await service.list_todos(user_id, offset=0, limit=2)
        assert len(items) == 2
        assert total == 5

        items, total = await service.list_todos(user_id, offset=4, limit=2)
        assert len(items) == 1
        assert total == 5

    async def test_update_title(self, db_session: AsyncSession) -> None:
        """update_todo changes the title and preserves other fields."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)
        todo = await service.create_todo(user_id, "Old", "Desc")

        updated = await service.update_todo(todo.id, user_id, title="New")
        assert updated.title == "New"
        assert updated.description == "Desc"
        assert updated.completed is False

    async def test_update_completed(self, db_session: AsyncSession) -> None:
        """update_todo can toggle the completed flag."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)
        todo = await service.create_todo(user_id, "Task", None)

        updated = await service.update_todo(todo.id, user_id, completed=True)
        assert updated.completed is True

    async def test_update_not_found(self, db_session: AsyncSession) -> None:
        """update_todo raises NotFoundError for a nonexistent todo."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)

        with pytest.raises(NotFoundError):
            await service.update_todo(9999, user_id, title="Nope")

    async def test_update_other_users_todo(self, db_session: AsyncSession) -> None:
        """update_todo raises NotFoundError when the todo belongs to another user."""
        service = self._make_service(db_session)
        user_id = await self._get_seed_user_id(db_session)
        todo = await service.create_todo(user_id, "Mine", None)

        with pytest.raises(NotFoundError):
            await service.update_todo(todo.id, 9999, title="Stolen")
