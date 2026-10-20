"""Request and response schemas for todos."""

import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateTodoRequest(BaseModel):
    """Data required to create a new todo."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)


class UpdateTodoRequest(BaseModel):
    """Data for updating an existing todo."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None

    @field_validator("title", "completed")
    @classmethod
    def _reject_explicit_null(cls, value: object) -> object:
        """Reject an explicit ``null`` for fields that cannot be cleared.

        Omitting a field keeps its value; only ``description`` may be set to
        ``null`` to clear it.
        """
        if value is None:
            raise ValueError("This field cannot be null.")
        return value


class BulkDeleteRequest(BaseModel):
    """IDs of todos to delete in bulk."""

    ids: list[int] = Field(min_length=1, max_length=100)


class BulkDeleteResponse(BaseModel):
    """Result of a bulk delete operation."""

    deleted: int


class MoveTodoRequest(BaseModel):
    """Data required to move a todo to another user."""

    target_user_id: int = Field(gt=0)


class TodoOut(BaseModel):
    """Public todo item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime.datetime
