import uuid
from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest


async def page(
    db: AsyncSession,
    *,
    status: str,
    start: date | None,
    end: date | None,
    employee_id: uuid.UUID | None,
    team_id: uuid.UUID | None,
    leave_type: str | None,
    after: tuple[date, uuid.UUID] | None,
    limit: int,
) -> list[tuple[LeaveRequest, Employee]]:
    """Ordered (start_date, id): stable for the keyset cursor, and the order HR reads a month."""
    q = (
        select(LeaveRequest, Employee)
        .join(Employee, Employee.id == LeaveRequest.employee_id)
        .where(LeaveRequest.status == status)
    )
    if start:
        q = q.where(LeaveRequest.end_date >= start)
    if end:
        q = q.where(LeaveRequest.start_date <= end)
    if employee_id:
        q = q.where(LeaveRequest.employee_id == employee_id)
    if team_id:
        q = q.where(Employee.team_id == team_id)
    if leave_type:
        q = q.where(LeaveRequest.leave_type_code == leave_type)
    if after:
        d, last_id = after
        q = q.where(
            or_(
                LeaveRequest.start_date > d,
                and_(LeaveRequest.start_date == d, LeaveRequest.id > last_id),
            )
        )
    result = await db.execute(q.order_by(LeaveRequest.start_date, LeaveRequest.id).limit(limit))
    return [(r, e) for r, e in result.all()]
