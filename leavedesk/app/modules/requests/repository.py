import uuid
from collections.abc import Collection
from datetime import date

from sqlalchemy import and_, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Employee
from app.modules.leave_days.calendar import HalfDay
from app.modules.leave_days.models import LeaveRequest, LeaveRequestDay


async def lock_employee(db: AsyncSession, employee_id: uuid.UUID) -> None:
    """Serialise one person's submits (spec 5.5): the second waits, then sees the first."""
    await db.scalar(select(Employee.id).where(Employee.id == employee_id).with_for_update())


async def get(db: AsyncSession, request_id: uuid.UUID) -> LeaveRequest | None:
    return await db.get(LeaveRequest, request_id)


async def find_overlap(
    db: AsyncSession, employee_id: uuid.UUID, rows: Collection[HalfDay]
) -> LeaveRequest | None:
    """The employee's own Pending/Approved request sharing a (date, slot) with `rows` (R13)."""
    if not rows:
        return None
    clash = tuple_(LeaveRequestDay.leave_date, LeaveRequestDay.slot).in_(
        [(d, s) for d, s, _ in rows]
    )
    return await db.scalar(
        select(LeaveRequest)
        .join(LeaveRequestDay, LeaveRequestDay.request_id == LeaveRequest.id)
        .where(LeaveRequestDay.employee_id == employee_id, LeaveRequestDay.is_active, clash)
        .order_by(LeaveRequest.start_date, LeaveRequest.id)
        .limit(1)
    )


def add(db: AsyncSession, req: LeaveRequest, rows: Collection[HalfDay]) -> None:
    db.add(req)
    db.add_all(
        LeaveRequestDay(
            request_id=req.id,
            leave_date=d,
            slot=s,
            employee_id=req.employee_id,
            leave_year=y,
            is_active=True,
        )
        for d, s, y in rows
    )


async def list_own(
    db: AsyncSession,
    employee_id: uuid.UUID,
    status: str | None,
    year: int | None,
    after: tuple[date, uuid.UUID] | None,
    limit: int,
) -> list[LeaveRequest]:
    q = select(LeaveRequest).where(LeaveRequest.employee_id == employee_id)
    if status:
        q = q.where(LeaveRequest.status == status)
    if year:
        q = q.where(
            LeaveRequest.start_date <= date(year, 12, 31), LeaveRequest.end_date >= date(year, 1, 1)
        )
    if after:
        start, last_id = after
        q = q.where(
            or_(
                LeaveRequest.start_date < start,
                and_(LeaveRequest.start_date == start, LeaveRequest.id > last_id),
            )
        )
    result = await db.scalars(
        q.order_by(LeaveRequest.start_date.desc(), LeaveRequest.id).limit(limit)
    )
    return list(result)
