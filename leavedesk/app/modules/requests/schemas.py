import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.core.schemas import StrictModel
from app.modules.leave_days.calendar import Part

LeaveTypeCode = Literal["annual", "sick", "unpaid"]
Status = Literal["pending", "approved", "rejected", "cancelled"]


def _blank_to_none(value: str | None) -> str | None:
    return (value or "").strip() or None


Note = Annotated[str | None, Field(max_length=500), AfterValidator(_blank_to_none)]


class RequestIn(StrictModel):
    """Body of `POST /requests` and `POST /requests/preview` (spec 6.2 #9, #10)."""

    leave_type: LeaveTypeCode
    start_date: date
    start_part: Part = "full"
    end_date: date
    end_part: Part = "full"
    note: Note = None


class CancelIn(StrictModel):
    """Body of `POST /requests/{id}/cancel` (spec 6.2 #12). HR must give a `reason` (R21)."""

    version: Annotated[int, Field(ge=1)]
    reason: Annotated[
        str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ] = None


class HrRequestIn(RequestIn):
    """Body of `POST /hr/requests` (spec 6.2 #17)."""

    employee_id: uuid.UUID
    entry_reason: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]


class RequestOut(BaseModel):
    """A request as one viewer may see it. `leave_type` and `note` are None when redacted (§8)."""

    id: uuid.UUID
    employee_id: uuid.UUID
    leave_type: str | None
    start_date: date
    start_part: str
    end_date: date
    end_part: str
    working_days: float
    note: str | None
    status: str
    queue: str
    assigned_to: uuid.UUID | None
    submitted_at: datetime
    notice_warning: bool
    version: int
    label: str | None = None  # "Off" while the Sick type is masked
    employee_name: str | None = None  # approvals lists only, for the deciding approver (R18)


class RequestList(BaseModel):
    items: list[RequestOut]
    next_cursor: str | None = None


class RuleIssue(BaseModel):
    code: str
    field: str | None
    message: str


class YearBalance(BaseModel):
    year: int
    days: float
    available_before: float | None  # None: the type has no balance (Unpaid)
    available_after: float | None


class PreviewOut(BaseModel):
    valid: bool
    working_days: float | None
    per_year: list[YearBalance]
    notice_warning: bool = False
    errors: list[RuleIssue]
