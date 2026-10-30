import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest, LeaveRequestDay


async def month_days(
    db: AsyncSession,
    start: date,
    end: date,
    team_id: uuid.UUID | None,
    include_inactive: bool,
) -> list[tuple[uuid.UUID, str, date, str, str, str]]:
    """Active half days of Pending and Approved requests between `start` and `end` inclusive:
    (employee_id, name, date, slot, leave_type, status). Ordered by date, name, slot, id: nothing
    that depends on the request itself, so the order cannot reveal which requests are Sick."""
    q = (
        select(
            Employee.id,
            Employee.name,
            LeaveRequestDay.leave_date,
            LeaveRequestDay.slot,
            LeaveRequest.leave_type_code,
            LeaveRequest.status,
        )
        .join(LeaveRequest, LeaveRequest.id == LeaveRequestDay.request_id)
        .join(Employee, Employee.id == LeaveRequestDay.employee_id)
        .where(
            LeaveRequestDay.is_active,
            LeaveRequestDay.leave_date.between(start, end),
            LeaveRequest.status.in_(("pending", "approved")),
        )
        .order_by(LeaveRequestDay.leave_date, Employee.name, LeaveRequestDay.slot, Employee.id)
    )
    if team_id is not None:
        q = q.where(Employee.team_id == team_id)
    if not include_inactive:
        q = q.where(Employee.is_active)  # R34: a deactivated person's history is HR-only
    return [tuple(r) for r in (await db.execute(q)).all()]  # type: ignore[misc]
