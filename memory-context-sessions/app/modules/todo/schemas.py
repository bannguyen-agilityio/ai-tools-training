"""Request and response schemas for todos."""

import datetime

from pydantic import BaseModel, Field


class CreateTodoRequest(BaseModel):
    """Data required to create a new todo."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)


class UpdateTodoRequest(BaseModel):
    """Data for updating an existing todo."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None


class BulkDeleteRequest(BaseModel):
    """IDs of todos to delete in bulk."""

    ids: list[int] = Field(min_length=1, max_length=100)


class BulkDeleteResponse(BaseModel):
    """Result of a bulk delete operation."""

    deleted: int


class MoveTodoRequest(BaseModel):
    """Data required to move a todo to another user."""

    target_user_id: int


class TodoOut(BaseModel):
    """Public todo item response."""

    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime.datetime
