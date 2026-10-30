import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class OffEntry(BaseModel):
    """Masked Sick leave (spec 6.1): exactly these keys, so Pending and Approved look the same
    and nothing reveals the type. No request id, no status, no link."""

    model_config = ConfigDict(extra="forbid")

    employee_id: uuid.UUID
    employee_name: str
    date: date
    slot: Literal["am", "pm"]
    label: Literal["Off"] = "Off"


class LeaveEntry(BaseModel):
    """Annual or Unpaid for a team viewer; any type for HR or the owner."""

    model_config = ConfigDict(extra="forbid")

    employee_id: uuid.UUID
    employee_name: str
    date: date
    slot: Literal["am", "pm"]
    leave_type: Literal["annual", "sick", "unpaid"]
    status: Literal["pending", "approved"]


class CalendarOut(BaseModel):
    month: str
    team_id: uuid.UUID | None
    entries: list[OffEntry | LeaveEntry]
