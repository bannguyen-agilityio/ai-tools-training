import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.core.schemas import StrictModel

Name = Annotated[str, Field(min_length=1, max_length=100)]
Email = Annotated[
    str,
    Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+$"),
    AfterValidator(str.lower),  # the DB domain CHECK is case-sensitive
]
Role = Literal["employee", "manager", "hr"]


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: str
    is_hr_deputy: bool
    team_id: uuid.UUID | None
    manager_id: uuid.UUID | None
    start_date: date
    end_date: date | None
    is_active: bool
    created_at: datetime


class EmployeeList(BaseModel):
    items: list[EmployeeOut]
    next_cursor: str | None = None


class EmployeeCreate(StrictModel):
    name: Name
    email: Email
    role: Role = "employee"
    team_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None
    start_date: date


class EmployeePatch(StrictModel):
    """Email and start date are not editable here (A-8; email is the login identity), and
    deactivation is its own action (#19)."""

    name: Name | None = None
    role: Role | None = None
    team_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _something_to_change(self) -> EmployeePatch:
        if not self.model_fields_set:
            raise ValueError("nothing to change")
        for field in ("name", "role"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
