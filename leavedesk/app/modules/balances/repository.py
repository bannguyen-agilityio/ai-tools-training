import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.balances.compute import DayUse
from app.modules.balances.models import BalanceEntry
from app.modules.identity.models import Employee


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


async def days_for(
    db: AsyncSession, employee_id: uuid.UUID, leave_type_code: str, leave_year: int
) -> list[DayUse]:
    """Approved and pending half days. `leave_request_day` arrives with plan 06 (R12), so
    until then there is no leave to count and this returns nothing."""
    return []
