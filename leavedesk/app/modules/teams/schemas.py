import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.schemas import StrictModel

Name = Annotated[str, Field(min_length=1, max_length=100)]


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    manager_id: uuid.UUID | None


class TeamList(BaseModel):
    items: list[TeamOut]
    next_cursor: str | None = None


class TeamCreate(StrictModel):
    name: Name
    manager_id: uuid.UUID | None = None


class TeamPatch(StrictModel):
    name: Name | None = None
    manager_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _something_to_change(self) -> TeamPatch:
        if not self.model_fields_set:
            raise ValueError("nothing to change")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self
