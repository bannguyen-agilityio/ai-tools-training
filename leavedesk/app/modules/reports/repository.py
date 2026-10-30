import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest, LeaveRequestDay


async def approved_days(
    db: AsyncSession, start: date, end: date
) -> list[tuple[uuid.UUID, uuid.UUID, str, str, date, date, date]]:
    """Active half days of Approved requests in [start, end]:
    (request_id, employee_id, employee name, leave type, request start, request end, leave date).
    Cancelled and rejected requests have no active day rows, and Pending is not leave taken."""
    result = await db.execute(
        select(
            LeaveRequest.id,
            Employee.id,
            Employee.name,
            LeaveRequest.leave_type_code,
            LeaveRequest.start_date,
            LeaveRequest.end_date,
            LeaveRequestDay.leave_date,
        )
        .join(LeaveRequestDay, LeaveRequestDay.request_id == LeaveRequest.id)
        .join(Employee, Employee.id == LeaveRequest.employee_id)
        .where(
            LeaveRequest.status == "approved",
            LeaveRequestDay.is_active,
            LeaveRequestDay.leave_date.between(start, end),
        )
        .order_by(Employee.name, Employee.id, LeaveRequest.start_date, LeaveRequest.id)
    )
    return [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in result.all()]
