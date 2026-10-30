import uuid
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.schemas import StrictModel

Name = Annotated[str, Field(min_length=1, max_length=100)]


class HolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    holiday_date: date
    name: str
    source: str


class HolidayCreate(StrictModel):
    holiday_date: date
    name: Name


class HolidayPatch(StrictModel):
    holiday_date: date | None = None
    name: Name | None = None

    @model_validator(mode="after")
    def _something_to_change(self) -> HolidayPatch:
        if self.holiday_date is None and self.name is None:
            raise ValueError("nothing to change")
        return self


class HolidayChangeOut(BaseModel):
    holiday: HolidayOut
    affected_requests: int


class ImpactOut(BaseModel):
    holiday_date: date
    affected_requests: int


class HolidayList(BaseModel):
    """Spec 6.1 list shape. One year is at most a few dozen rows, so there is never a next page."""

    items: list[HolidayOut]
    next_cursor: str | None = None
