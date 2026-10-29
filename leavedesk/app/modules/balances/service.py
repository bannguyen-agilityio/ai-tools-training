import uuid
from collections.abc import Awaitable, Callable
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.balances import repository
from app.modules.balances.compute import DayUse, Entry, compute_balance

# Allowances and cap mirror the seeded `leave_type` rows (R5, spec 5.1).
ALLOWANCE = {"annual": Decimal(12), "sick": Decimal(7)}
CARRY_CAP = Decimal(6)

DaysLoader = Callable[[AsyncSession, uuid.UUID, str, int], Awaitable[list[DayUse]]]


def _entries(rows: list) -> list[Entry]:  # type: ignore[type-arg]
    return [Entry(kind=r.kind, days=r.days, expires_on=r.expires_on) for r in rows]


async def rollover(db: AsyncSession, year: int, load_days: DaysLoader = repository.days_for) -> int:
    """1 Jan job: write `year`'s entitlement and the Annual carry-over (R5, R7, R8).

    Sick never carries. Carry = min(6, unused entitlement of the previous year); carried days
    of that year are ignored so nothing is carried twice. Returns the number of rows written.
    """
    written = 0
    today = date(year, 1, 1)
    for emp in await repository.active_employees(db):
        if emp.start_date.year < year:
            for code, days in ALLOWANCE.items():
                written += await repository.add_entry(
                    db,
                    employee_id=emp.id,
                    leave_type_code=code,
                    leave_year=year,
                    kind="entitlement",
                    days=days,
                    idempotency_key=f"entitlement:{year}:{emp.id}:{code}",
                )
        rows = await repository.entries_for(db, emp.id, "annual", year - 1)
        if not rows:
            continue
        previous = compute_balance(
            _entries(rows), await load_days(db, emp.id, "annual", year - 1), today
        )
        carry = min(CARRY_CAP, previous.unused_entitlement)
        if carry > 0:
            written += await repository.add_entry(
                db,
                employee_id=emp.id,
                leave_type_code="annual",
                leave_year=year,
                kind="carry_over",
                days=carry,
                expires_on=date(year, 12, 31),
                idempotency_key=f"rollover:{year}:{emp.id}",
            )
    await db.commit()
    return written


async def expire_carry(
    db: AsyncSession, today: date, load_days: DaysLoader = repository.days_for
) -> int:
    """Daily job: record an `expiry` entry for unused carried days past `expires_on` (R7).

    The balance is already correct without it (compute_balance derives expiry); the entry is
    the audit record. Returns the number of rows written.
    """
    written = 0
    for emp in await repository.active_employees(db):
        for year in (today.year, today.year - 1):
            rows = await repository.entries_for(db, emp.id, "annual", year)
            if not any(r.kind == "carry_over" for r in rows):
                continue
            balance = compute_balance(
                _entries(rows), await load_days(db, emp.id, "annual", year), today
            )
            if balance.expirable_carried > 0:
                written += await repository.add_entry(
                    db,
                    employee_id=emp.id,
                    leave_type_code="annual",
                    leave_year=year,
                    kind="expiry",
                    days=-balance.expirable_carried,
                    idempotency_key=f"expiry:{year}:{emp.id}",
                )
    await db.commit()
    return written
