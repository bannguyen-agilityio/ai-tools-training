import calendar as pycal
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.calendar import repository
from app.modules.calendar.masking import entry_for
from app.modules.calendar.schemas import CalendarOut
from app.modules.identity.models import Employee


def parse_month(month: str) -> tuple[date, date]:
    year, mon = (int(part) for part in month.split("-"))
    return date(year, mon, 1), date(year, mon, pycal.monthrange(year, mon)[1])


async def month_view(
    db: AsyncSession, viewer: Employee, month: str, team_id: uuid.UUID | None
) -> CalendarOut:
    """HR sees any team (all teams without `team_id`); everyone else only their own (A-21)."""
    is_hr = viewer.role == "hr"
    if not is_hr:
        if team_id is not None and team_id != viewer.team_id:
            raise ProblemError(403, "You can only see your own team's calendar.")
        team_id = viewer.team_id
        if team_id is None:
            return CalendarOut(month=month, team_id=None, entries=[])
    start, end = parse_month(month)
    rows = await repository.month_days(db, start, end, team_id, include_inactive=is_hr)
    return CalendarOut(
        month=month,
        team_id=team_id,
        entries=[
            entry_for(
                viewer,
                employee_id=eid,
                employee_name=name,
                day=day,
                slot=slot,
                leave_type=leave_type,
                status=status,
            )
            for eid, name, day, slot, leave_type, status in rows
        ],
    )
