"""HTTP endpoints for todos."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_pagination_meta,
)
from app.modules.todo.dependencies import get_current_user_id, get_todo_service
from app.modules.todo.schemas import CreateTodoRequest, TodoOut, UpdateTodoRequest
from app.modules.todo.service import TodoService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TodoOut])
async def list_todos(
    user_id: Annotated[int, Depends(get_current_user_id)],
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[TodoOut]:
    """Return a paginated list of todos for the authenticated user.

    Args:
        user_id: The current user's database ID.
        todo_service: The todo service.
        pagination: Pagination query parameters.

    Returns:
        A paginated list of the user's todos.
    """
    todos, total = await todo_service.list_todos(
        user_id, offset=pagination.offset, limit=pagination.page_size
    )
    items = [
        TodoOut(
            id=t.id,
            title=t.title,
            description=t.description,
            completed=t.completed,
            created_at=t.created_at,
        )
        for t in todos
    ]
    meta = build_pagination_meta(
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.post("", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(
    body: CreateTodoRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoOut:
    """Create a new todo for the authenticated user.

    Args:
        body: The todo data.
        user_id: The current user's database ID.
        todo_service: The todo service.

    Returns:
        The newly created todo.
    """
    todo = await todo_service.create_todo(user_id, body.title, body.description)
    return TodoOut(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        created_at=todo.created_at,
    )


@router.patch("/{todo_id}", response_model=TodoOut)
async def update_todo(
    todo_id: int,
    body: UpdateTodoRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoOut:
    """Update an existing todo for the authenticated user.

    Args:
        todo_id: The ID of the todo to update.
        body: The fields to update.
        user_id: The current user's database ID.
        todo_service: The todo service.

    Returns:
        The updated todo.
    """
    todo = await todo_service.update_todo(
        todo_id,
        user_id,
        title=body.title,
        description=body.description,
        completed=body.completed,
    )
    return TodoOut(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        created_at=todo.created_at,
    )
