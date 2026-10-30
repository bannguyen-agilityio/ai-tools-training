import base64
import binascii
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.hr_leave import repository
from app.modules.hr_leave.schemas import HrLeaveList, HrLeaveOut
from app.modules.identity.models import Employee


def _decode(cursor: str | None) -> tuple[date, uuid.UUID] | None:
    if not cursor:
        return None
    try:
        start, last_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return date.fromisoformat(start), uuid.UUID(last_id)
    except (ValueError, binascii.Error) as exc:
        raise ProblemError(422, "Invalid cursor") from exc


async def list_leave(
    db: AsyncSession,
    actor: Employee,
    *,
    status: str,
    start: date | None,
    end: date | None,
    employee_id: uuid.UUID | None,
    team_id: uuid.UUID | None,
    leave_type: str | None,
    limit: int,
    cursor: str | None,
) -> HrLeaveList:
    # Defence in depth: the route dependency requires HR; the deputy has no admin rights (R36).
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")
    if start and end and end < start:
        raise ProblemError(422, "The end of the range is before its start.")
    rows = await repository.page(
        db,
        status=status,
        start=start,
        end=end,
        employee_id=employee_id,
        team_id=team_id,
        leave_type=leave_type,
        after=_decode(cursor),
        limit=limit + 1,
    )
    shown = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last = shown[-1][0]
        next_cursor = base64.urlsafe_b64encode(
            f"{last.start_date.isoformat()}|{last.id}".encode()
        ).decode()
    return HrLeaveList(
        items=[
            HrLeaveOut(
                id=r.id,
                employee_id=r.employee_id,
                employee_name=e.name,
                team_id=e.team_id,
                leave_type=r.leave_type_code,
                start_date=r.start_date,
                start_part=r.start_part,
                end_date=r.end_date,
                end_part=r.end_part,
                working_days=float(r.working_days),
                note=r.note,
                status=r.status,
                version=r.version,
            )
            for r, e in shown
        ],
        next_cursor=next_cursor,
    )
