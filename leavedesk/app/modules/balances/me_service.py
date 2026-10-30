from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.balances import repository
from app.modules.balances.compute import compute_balance
from app.modules.balances.schemas import MyBalances, TypeBalance
from app.modules.balances.service import entries_of
from app.modules.identity.models import Employee

LIMITED_TYPES = ("annual", "sick")  # Unpaid has no balance (R10)


async def my_balances(db: AsyncSession, employee: Employee, year: int, today: date) -> MyBalances:
    """The caller's own balances; every number comes from `compute_balance`."""
    out: list[TypeBalance] = []
    for code in LIMITED_TYPES:
        rows = await repository.entries_for(db, employee.id, code, year)
        days = await repository.days_for(db, employee.id, code, year)
        b = compute_balance(entries_of(rows), days, today)
        out.append(
            TypeBalance(
                leave_type=code,
                entitlement=float(b.entitlement),
                carried=float(b.carried),
                expires_on=b.carried_expires_on,
                carried_expired=b.carried_expires_on is not None and today > b.carried_expires_on,
                used=float(b.used),
                reserved=float(b.reserved),
                available=float(b.available),
            )
        )
    return MyBalances(year=year, balances=out)
