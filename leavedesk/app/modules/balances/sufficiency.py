"""Sufficiency check for Annual and Sick requests (R10). Plan 10 calls it from submit."""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.balances import repository
from app.modules.balances.compute import compute_balance
from app.modules.balances.models import LeaveType
from app.modules.balances.service import entries_of
from app.modules.identity.models import Employee


async def ensure_sufficient(
    db: AsyncSession,
    employee: Employee,
    leave_type_code: str,
    requested_days_per_year: dict[int, Decimal],
    today: date,
) -> None:
    """Raise 422 `INSUFFICIENT_BALANCE` stating the shortfall when a limited type would go below 0.

    A request spanning two years is checked against each year's own balance; carried days are
    consumed first inside `compute_balance`. Exactly zero left is allowed. Unpaid is never blocked.
    """
    leave_type = await db.get(LeaveType, leave_type_code)
    if leave_type is None or not leave_type.is_limited:
        return
    for year, requested in sorted(requested_days_per_year.items()):
        rows = await repository.entries_for(db, employee.id, leave_type_code, year)
        days = await repository.days_for(db, employee.id, leave_type_code, year)
        shortfall = requested - compute_balance(entries_of(rows), days, today).available
        if shortfall > 0:
            raise ProblemError(
                422,
                f"Not enough {leave_type_code} leave in {year}: short by {shortfall:g} "
                f"day{'' if shortfall == 1 else 's'}.",
                code="INSUFFICIENT_BALANCE",
            )
