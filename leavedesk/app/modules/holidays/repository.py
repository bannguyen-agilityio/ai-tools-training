import uuid
from collections.abc import Collection
from datetime import date

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.holidays.models import PublicHoliday
from app.modules.leave_days.models import LeaveRequest

SATURDAY = 5


async def list_year(db: AsyncSession, year: int) -> list[PublicHoliday]:
    result = await db.execute(
        select(PublicHoliday)
        .where(PublicHoliday.holiday_date.between(date(year, 1, 1), date(year, 12, 31)))
        .order_by(PublicHoliday.holiday_date)
    )
    return list(result.scalars())


async def dates_between(db: AsyncSession, start: date, end: date) -> frozenset[date]:
    result = await db.scalars(
        select(PublicHoliday.holiday_date).where(PublicHoliday.holiday_date.between(start, end))
    )
    return frozenset(result)


async def get(db: AsyncSession, holiday_id: uuid.UUID) -> PublicHoliday | None:
    return await db.get(PublicHoliday, holiday_id)


async def get_by_date(db: AsyncSession, holiday_date: date) -> PublicHoliday | None:
    return await db.scalar(select(PublicHoliday).where(PublicHoliday.holiday_date == holiday_date))


async def add(db: AsyncSession, holiday: PublicHoliday) -> PublicHoliday:
    db.add(holiday)
    await db.flush()
    return holiday


async def remove(db: AsyncSession, holiday_id: uuid.UUID) -> bool:
    """False when a concurrent delete already removed the row."""
    result = await db.execute(delete(PublicHoliday).where(PublicHoliday.id == holiday_id))
    return bool(result.rowcount)  # type: ignore[attr-defined]


async def count_affected(db: AsyncSession, dates: Collection[date]) -> int:
    """Pending or Approved requests whose range covers a weekday in `dates` (C-8).

    Range-based, not day-row based, so it also counts requests that skipped the date because
    it was a holiday (a deleted holiday would now count as a working day for them). Weekend
    dates are ignored: a holiday on a Saturday or Sunday changes no count.
    """
    weekdays = [d for d in dates if d.weekday() < SATURDAY]
    if not weekdays:
        return 0
    covers = or_(
        *(and_(LeaveRequest.start_date <= d, LeaveRequest.end_date >= d) for d in weekdays)
    )
    return (
        await db.scalar(
            select(func.count())
            .select_from(LeaveRequest)
            .where(LeaveRequest.status.in_(("pending", "approved")), covers)
        )
    ) or 0
