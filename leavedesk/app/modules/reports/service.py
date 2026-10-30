import calendar as pycal
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.balances import repository as ledger
from app.modules.balances.compute import DayUse, compute_balance
from app.modules.balances.service import entries_of
from app.modules.identity.models import Employee
from app.modules.reports import repository
from app.modules.reports.schemas import BalanceRow, MonthlyReport, OffRow, SummaryRow

HALF = Decimal("0.5")
TYPE_ORDER = {"annual": 0, "sick": 1, "unpaid": 2}


def month_bounds(month: str) -> tuple[date, date]:
    year, mon = (int(part) for part in month.split("-"))
    return date(year, mon, 1), date(year, mon, pycal.monthrange(year, mon)[1])


def _taken_by(days: list[DayUse], end: date) -> list[DayUse]:
    return [d for d in days if d.status == "approved" and d.leave_date <= end]


async def build(db: AsyncSession, actor: Employee, month: str) -> MonthlyReport:
    # Defence in depth: the route dependency requires HR; the deputy has no export rights (R36).
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")
    start, end = month_bounds(month)
    report = MonthlyReport(month=month)

    taken: dict[tuple[uuid.UUID, str], Decimal] = defaultdict(Decimal)
    names: dict[uuid.UUID, str] = {}
    spans: dict[object, tuple[str, str, date, date, Decimal]] = {}
    for rid, eid, name, code, r_start, r_end, _day in await repository.approved_days(
        db, start, end
    ):
        names[eid] = name
        taken[(eid, code)] += HALF  # one row per half day; grouped by id, so equal names stay apart
        _, _, _, _, so_far = spans.get(rid, (name, code, r_start, r_end, Decimal(0)))
        spans[rid] = (name, code, r_start, r_end, so_far + HALF)
        report.request_ids.add(rid)
    report.summary = [
        SummaryRow(names[eid], code, days)
        for (eid, code), days in sorted(
            taken.items(), key=lambda kv: (names[kv[0][0]], kv[0][0], TYPE_ORDER[kv[0][1]])
        )
    ]
    report.off = sorted(
        (OffRow(n, c, s, e, d) for n, c, s, e, d in spans.values()),
        key=lambda r: (r.start_date, r.employee, r.leave_type),
    )

    # Balances as of the last day of the month, for that leave year (A-20): only Approved days up
    # to `end` count, so later leave and Pending reservations never change an old month.
    year = start.year
    entries = await ledger.entries_by_employee(db, year)
    annual_days = await ledger.days_by_employee(db, "annual", year)
    sick_days = await ledger.days_by_employee(db, "sick", year)
    for employee in await ledger.employees_by_name(db):
        annual = compute_balance(
            entries_of(entries.get((employee.id, "annual"), [])),
            _taken_by(annual_days.get(employee.id, []), end),
            end,
        )
        sick = compute_balance(
            entries_of(entries.get((employee.id, "sick"), [])),
            _taken_by(sick_days.get(employee.id, []), end),
            end,
        )
        report.balances.append(
            BalanceRow(employee.name, annual.available, annual.carried_remaining, sick.available)
        )
    return report
