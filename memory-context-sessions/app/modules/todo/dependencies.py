"""Dependency injection for the todo module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database import get_db_session
from app.modules.auth.dependencies import get_auth_service, get_current_user
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService
from app.modules.todo.repository import TodoRepository
from app.modules.todo.service import TodoService


def get_todo_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TodoRepository:
    """Provide a todo repository backed by the request database session."""
    return TodoRepository(session)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    """Provide a user repository backed by the request database session."""
    return UserRepository(session)


def get_todo_service(
    todo_repo: Annotated[TodoRepository, Depends(get_todo_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> TodoService:
    """Provide the todo service with its repository dependencies."""
    return TodoService(todo_repo, user_repo)


async def get_current_user_id(
    username: Annotated[str, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> int:
    """Resolve the current user's database ID from the bearer token.

    Args:
        username: The authenticated username.
        auth_service: The authentication service.

    Returns:
        The user's database ID.

    Raises:
        NotFoundError: If the user no longer exists.
    """
    user = await auth_service.get_user(username)
    if not user:
        raise NotFoundError(message="User not found", code="USER_NOT_FOUND")
    return user.id
