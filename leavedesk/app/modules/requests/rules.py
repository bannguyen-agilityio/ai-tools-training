"""Validation pipeline shared by preview and submit (R12, R13, R6, R10).

Order: shape -> past date -> working days -> sufficiency -> overlap. Each step returns a
`ProblemError`; `evaluate` collects them so preview can show every problem, and submit raises
the first. Notice rules and Sick limits beyond the backdate window belong to plan 11.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.balances.models import LeaveType
from app.modules.balances.sufficiency import available_by_year, insufficient
from app.modules.email.privacy import date_range
from app.modules.identity.models import Employee
from app.modules.leave_days.calendar import HalfDay, days_per_year
from app.modules.leave_days.service import working_half_days
from app.modules.requests import repository
from app.modules.requests.schemas import RequestIn


@dataclass
class Evaluation:
    rows: list[HalfDay] = field(default_factory=list)
    per_year: dict[int, Decimal] = field(default_factory=dict)
    available_before: dict[int, Decimal] | None = None  # None: type has no balance
    errors: list[ProblemError] = field(default_factory=list)

    @property
    def working_days(self) -> Decimal | None:
        return sum(self.per_year.values(), Decimal(0)) if self.rows else None


def _field_error(status: int, code: str, field_name: str, message: str) -> ProblemError:
    return ProblemError(
        status, message, code=code, details=[{"field": field_name, "issue": message}]
    )


def check_shape(body: RequestIn) -> ProblemError | None:
    """End before start, and the Q7 half-day shapes. Field-specific so the UI can mark it."""
    if body.end_date < body.start_date:
        return _field_error(422, "END_BEFORE_START", "end_date", "End date is before start date.")
    if body.start_date == body.end_date:
        if body.start_part != body.end_part:
            return _field_error(
                422, "INVALID_PARTS", "end_part", "A single day needs the same start and end part."
            )
    elif body.start_part == "am":
        return _field_error(
            422, "INVALID_PARTS", "start_part", "A multi-day request cannot start in the morning."
        )
    elif body.end_part == "pm":
        return _field_error(
            422, "INVALID_PARTS", "end_part", "A multi-day request cannot end in the afternoon."
        )
    return None


async def check_past(db: AsyncSession, body: RequestIn, today: date) -> ProblemError | None:
    """Annual and Unpaid cannot start in the past (R13); Sick may go back its backdate window
    (R15, `leave_type.allow_backdate_days`)."""
    leave_type = await db.get(LeaveType, body.leave_type)
    backdate = leave_type.allow_backdate_days if leave_type else 0
    if (today - body.start_date).days > backdate:
        message = (
            "Start date is in the past."
            if backdate == 0
            else f"Start date is more than {backdate} days in the past. Ask HR to enter it."
        )
        return _field_error(422, "START_IN_PAST", "start_date", message)
    return None


async def check_overlap(
    db: AsyncSession, employee: Employee, rows: list[HalfDay]
) -> ProblemError | None:
    clash = await repository.find_overlap(db, employee.id, rows)
    if clash is None:
        return None
    # Names the conflicting request by dates and status, never its type or note.
    message = (
        f"This overlaps your {clash.status} leave for "
        f"{date_range(clash.start_date, clash.end_date)}."
    )
    return ProblemError(
        409, message, code="OVERLAP", details=[{"field": "start_date", "issue": message}]
    )


async def evaluate(
    db: AsyncSession, employee: Employee, body: RequestIn, today: date
) -> Evaluation:
    ev = Evaluation()
    shape = check_shape(body)
    if shape is not None:
        ev.errors.append(shape)
        return ev
    past = await check_past(db, body, today)
    if past is not None:
        ev.errors.append(past)
    try:
        ev.rows = await working_half_days(
            db, body.start_date, body.start_part, body.end_date, body.end_part
        )
    except ProblemError as exc:
        ev.errors.append(exc)
        return ev
    ev.per_year = days_per_year(ev.rows)

    leave_type = await db.get(LeaveType, body.leave_type)
    if leave_type is not None and leave_type.is_limited:
        ev.available_before = await available_by_year(
            db, employee, body.leave_type, ev.per_year, today
        )
        for year, requested in sorted(ev.per_year.items()):
            shortfall = requested - ev.available_before[year]
            if shortfall > 0:
                ev.errors.append(insufficient(body.leave_type, year, shortfall))
                break

    overlap = await check_overlap(db, employee, ev.rows)
    if overlap is not None:
        ev.errors.append(overlap)
    return ev
