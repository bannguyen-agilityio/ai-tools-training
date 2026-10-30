import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel

Status = Literal["pending", "approved", "rejected", "cancelled"]
LeaveType = Literal["annual", "sick", "unpaid"]
Part = Literal["full", "am", "pm"]


class HrLeaveOut(BaseModel):
    """One row for HR: the real type and the note are included (the HR column of spec §8)."""

    id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str
    team_id: uuid.UUID | None
    leave_type: LeaveType
    start_date: date
    start_part: Part
    end_date: date
    end_part: Part
    working_days: float
    note: str | None
    status: Status
    version: int


class HrLeaveList(BaseModel):
    items: list[HrLeaveOut]
    next_cursor: str | None = None
