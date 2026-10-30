import uuid
from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.balances.compute import DayUse
from app.modules.balances.models import BalanceEntry
from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest, LeaveRequestDay


async def add_entry(
    db: AsyncSession,
    *,
    employee_id: uuid.UUID,
    leave_type_code: str,
    leave_year: int,
    kind: str,
    days: Decimal,
    expires_on: date | None = None,
    reason: str | None = None,
    source: str = "system",
    idempotency_key: str | None = None,
    corrects_entry_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
) -> bool:
    """Append one ledger row. Returns False when the idempotency key already exists."""
    stmt = (
        insert(BalanceEntry)
        .values(
            employee_id=employee_id,
            leave_type_code=leave_type_code,
            leave_year=leave_year,
            kind=kind,
            days=days,
            expires_on=expires_on,
            reason=reason,
            source=source,
            idempotency_key=idempotency_key,
            corrects_entry_id=corrects_entry_id,
            created_by=created_by,
        )
        .on_conflict_do_nothing(index_elements=["idempotency_key"])
        .returning(BalanceEntry.id)
    )
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def entries_for(
    db: AsyncSession, employee_id: uuid.UUID, leave_type_code: str, leave_year: int
) -> list[BalanceEntry]:
    result = await db.execute(
        select(BalanceEntry).where(
            BalanceEntry.employee_id == employee_id,
            BalanceEntry.leave_type_code == leave_type_code,
            BalanceEntry.leave_year == leave_year,
        )
    )
    return list(result.scalars())


async def active_employees(db: AsyncSession) -> list[Employee]:
    result = await db.execute(select(Employee).where(Employee.is_active))
    return list(result.scalars())


def _day_uses(rows: Iterable[tuple[date, str]]) -> list[DayUse]:
    return [
        DayUse(leave_date=d, status="approved" if status == "approved" else "pending")
        for d, status in rows
    ]


def _active_days(leave_type_code: str, leave_year: int):  # type: ignore[no-untyped-def]
    return (
        select(LeaveRequestDay.employee_id, LeaveRequestDay.leave_date, LeaveRequest.status)
        .join(LeaveRequest, LeaveRequest.id == LeaveRequestDay.request_id)
        .where(
            LeaveRequestDay.leave_year == leave_year,
            LeaveRequestDay.is_active,
            LeaveRequest.leave_type_code == leave_type_code,
            LeaveRequest.status.in_(("pending", "approved")),
        )
    )


async def days_for(
    db: AsyncSession, employee_id: uuid.UUID, leave_type_code: str, leave_year: int
) -> list[DayUse]:
    """Approved and pending half days from `leave_request_day` (spec 5.4).

    Only active rows of pending or approved requests count, one `DayUse` per half day."""
    result = await db.execute(
        _active_days(leave_type_code, leave_year).where(LeaveRequestDay.employee_id == employee_id)
    )
    return _day_uses((d, status) for _, d, status in result.all())


async def days_by_employee(
    db: AsyncSession, leave_type_code: str, leave_year: int
) -> dict[uuid.UUID, list[DayUse]]:
    """`days_for` for every employee in one query (the jobs walk all active employees)."""
    grouped: dict[uuid.UUID, list[tuple[date, str]]] = defaultdict(list)
    for employee_id, d, status in (
        await db.execute(_active_days(leave_type_code, leave_year))
    ).all():
        grouped[employee_id].append((d, status))
    return {employee_id: _day_uses(rows) for employee_id, rows in grouped.items()}
