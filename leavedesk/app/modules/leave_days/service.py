from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.holidays import repository as holidays
from app.modules.leave_days.calendar import HalfDay, Part, expand_days

NO_WORKING_DAYS = "This range has no working days."


async def working_half_days(
    db: AsyncSession, start: date, start_part: Part, end: date, end_part: Part
) -> list[HalfDay]:
    """The shared validator (R6): expand the range against the stored holidays.

    A range with no working day (weekend or holiday only) is refused with 422
    `NO_WORKING_DAYS`. Plan 10's preview and submit call this, so the rule lives once.
    """
    try:
        rows = expand_days(
            start, start_part, end, end_part, await holidays.dates_between(db, start, end)
        )
    except ValueError as exc:
        raise ProblemError(422, "Invalid date range", code="INVALID_RANGE") from exc
    if not rows:
        raise ProblemError(422, NO_WORKING_DAYS, code="NO_WORKING_DAYS")
    return rows
