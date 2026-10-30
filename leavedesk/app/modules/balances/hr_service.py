import uuid
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.balances import repository
from app.modules.balances.compute import Balance, compute_balance
from app.modules.balances.hr_schemas import (
    CARRY_CAP,
    BalanceList,
    BalanceOut,
    BalanceRow,
    EmployeeBalances,
    EntryIn,
    EntryOut,
    Summary,
)
from app.modules.balances.models import BalanceEntry
from app.modules.balances.service import entries_of
from app.modules.identity.models import Employee

TYPES = ("annual", "sick")


def _require_hr(actor: Employee) -> None:
    # Defence in depth: the route dependency already requires HR; the deputy has no admin rights.
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")


def _today() -> date:
    return datetime.now(ZoneInfo(get_settings().company_tz)).date()


def _out(code: str, balance: Balance) -> BalanceOut:
    return BalanceOut(
        leave_type_code=code,
        entitlement_remaining=balance.entitlement_remaining,
        carried_remaining=balance.carried_remaining,
        used=balance.used,
        reserved=balance.reserved,
        available=balance.available,
    )


async def _balance(
    db: AsyncSession, employee_id: uuid.UUID, code: str, year: int, extra: list[BalanceEntry]
) -> Balance:
    rows = [*await repository.entries_for(db, employee_id, code, year), *extra]
    days = await repository.days_for(db, employee_id, code, year)
    return compute_balance(entries_of(rows), days, _today())


async def _employee(db: AsyncSession, employee_id: uuid.UUID) -> Employee:
    employee = await repository.get_employee(db, employee_id)
    if employee is None:
        raise ProblemError(404, "Employee not found")
    return employee


def _build(employee: Employee, body: EntryIn, actor: Employee) -> BalanceEntry:
    year = body.leave_year or _today().year
    if body.expires_on is not None and body.expires_on.year != year:
        raise ProblemError(422, "expires_on must fall in the leave year of the entry.")
    return BalanceEntry(
        employee_id=employee.id,
        leave_type_code=body.leave_type_code,
        leave_year=year,
        kind=body.kind,
        days=body.days,
        expires_on=body.expires_on,
        reason=body.reason,
        source="manual",
        corrects_entry_id=body.corrects_entry_id,
        created_by=actor.id,
    )


async def _check_corrects(db: AsyncSession, employee: Employee, entry: BalanceEntry) -> None:
    if entry.corrects_entry_id is None:
        return
    original = await db.get(BalanceEntry, entry.corrects_entry_id)
    if (
        original is None
        or original.employee_id != employee.id
        or original.leave_type_code != entry.leave_type_code
        or original.leave_year != entry.leave_year
    ):
        raise ProblemError(
            422, "corrects_entry_id must be an entry of this employee, leave type and year."
        )


async def _check_not_duplicate(db: AsyncSession, entry: BalanceEntry) -> None:
    """A second opening or manual carry-over would silently double the balance (C-9); the
    ledger is append-only, so the fix would be another entry. Corrections are adjustments."""
    if entry.kind not in ("opening", "carry_over"):
        return
    rows = await repository.entries_for(
        db, entry.employee_id, entry.leave_type_code, entry.leave_year
    )
    if any(r.kind == entry.kind and r.source == "manual" for r in rows):
        raise ProblemError(
            409, "That entry already exists for this employee. Add a correction instead."
        )
    if entry.kind == "carry_over" and (
        sum((r.days for r in rows if r.kind == "carry_over"), Decimal(0)) + entry.days > CARRY_CAP
    ):
        # Manual plus rollover carry must not stack past the cap (R7).
        raise ProblemError(409, "Carry-over for this year would exceed 6 days.")


async def preview(
    db: AsyncSession, actor: Employee, employee_id: uuid.UUID, body: EntryIn
) -> Summary:
    """Dry run: nothing is written (the entry is built but never added to the session)."""
    _require_hr(actor)
    employee = await _employee(db, employee_id)
    entry = _build(employee, body, actor)
    await _check_corrects(db, employee, entry)
    await _check_not_duplicate(db, entry)
    balance = await _balance(db, employee.id, entry.leave_type_code, entry.leave_year, [entry])
    return Summary(
        employee_id=employee.id,
        employee_name=employee.name,
        leave_type_code=entry.leave_type_code,
        leave_year=entry.leave_year,
        kind=entry.kind,
        days=entry.days,
        expires_on=entry.expires_on,
        resulting_available=balance.available,
    )


async def create(
    db: AsyncSession, actor: Employee, employee_id: uuid.UUID, body: EntryIn, ip: str | None
) -> BalanceEntry:
    _require_hr(actor)
    employee = await _employee(db, employee_id)
    entry = _build(employee, body, actor)
    await _check_corrects(db, employee, entry)
    await _check_not_duplicate(db, entry)
    await repository.add_manual(db, entry)
    # No leave type, reason or note in the audit detail (R30, privacy): ids, year and days only.
    await audit.record(
        db,
        actor_id=actor.id,
        action="balance.entry_create",
        target_type="balance_entry",
        target_id=str(entry.id),
        detail={
            "employee_id": str(employee.id),
            "leave_year": entry.leave_year,
            "days": str(entry.days),
        },
        ip=ip,
    )
    await db.commit()
    return entry


async def employee_balances(
    db: AsyncSession, actor: Employee, employee_id: uuid.UUID, year: int | None
) -> EmployeeBalances:
    _require_hr(actor)
    employee = await _employee(db, employee_id)
    year = year or _today().year
    balances = [_out(c, await _balance(db, employee.id, c, year, [])) for c in TYPES]
    ledger = await repository.ledger_for(db, employee.id, year)
    return EmployeeBalances(
        employee_id=employee.id,
        employee_name=employee.name,
        leave_year=year,
        balances=balances,
        ledger=[EntryOut.model_validate(r) for r in ledger],
    )


async def all_balances(db: AsyncSession, actor: Employee, year: int | None) -> BalanceList:
    """Every active employee: the printable "balances at launch" list (C-9)."""
    _require_hr(actor)
    year = year or _today().year
    entries = await repository.entries_by_employee(db, year)
    days = {c: await repository.days_by_employee(db, c, year) for c in TYPES}
    today = _today()
    items = [
        BalanceRow(
            employee_id=e.id,
            employee_name=e.name,
            email=e.email,
            balances=[
                _out(
                    c,
                    compute_balance(
                        entries_of(entries.get((e.id, c), [])), days[c].get(e.id, []), today
                    ),
                )
                for c in TYPES
            ],
        )
        for e in await repository.employees_by_name(db)
    ]
    return BalanceList(leave_year=year, items=items)
