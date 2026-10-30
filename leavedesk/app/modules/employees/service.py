import base64
import binascii
import uuid
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.auth import service as auth
from app.modules.balances import repository as ledger
from app.modules.balances.service import ALLOWANCE
from app.modules.employees import repository
from app.modules.employees.prorata import prorata
from app.modules.employees.schemas import EmployeeCreate, EmployeePatch
from app.modules.identity.models import Employee

TARGET = "employee"
DUPLICATE = "An employee with that email already exists."


def _require_hr(actor: Employee) -> None:
    # Defence in depth: the route dependency already requires HR; the deputy has no admin rights.
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")


def _snapshot(employee: Employee) -> dict[str, Any]:
    return {
        "role": employee.role,
        "team_id": str(employee.team_id) if employee.team_id else None,
        "manager_id": str(employee.manager_id) if employee.manager_id else None,
        "start_date": employee.start_date.isoformat(),
        "is_active": employee.is_active,
    }


def _today_year() -> int:
    return datetime.now(ZoneInfo(get_settings().company_tz)).year


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        offset = int(base64.urlsafe_b64decode(cursor.encode()))
    except (ValueError, binascii.Error) as exc:
        raise ProblemError(422, "Invalid cursor") from exc
    if offset < 0:
        raise ProblemError(422, "Invalid cursor")
    return offset


async def _get(db: AsyncSession, employee_id: uuid.UUID) -> Employee:
    employee = await repository.get(db, employee_id)
    if employee is None:
        raise ProblemError(404, "Employee not found")
    return employee


async def _check_team(db: AsyncSession, team_id: uuid.UUID | None) -> None:
    if team_id is not None and await repository.get_team(db, team_id) is None:
        raise ProblemError(422, "Team does not exist")


async def _check_manager(
    db: AsyncSession, manager_id: uuid.UUID | None, employee_id: uuid.UUID | None
) -> None:
    """The manager must be another active employee and must not (transitively) report to
    `employee_id`: A -> B -> A and longer cycles are refused (R23)."""
    if manager_id is None:
        return
    if manager_id == employee_id:
        raise ProblemError(422, "An employee cannot be their own manager.")
    manager = await repository.get(db, manager_id)
    if manager is None or not manager.is_active:
        raise ProblemError(422, "Manager must be an active employee.")
    if employee_id is None:
        return
    seen: set[uuid.UUID] = set()
    node: uuid.UUID | None = manager_id
    while node is not None and node not in seen:
        if node == employee_id:
            raise ProblemError(422, "That manager would create a reporting loop.")
        seen.add(node)
        node = await repository.manager_of(db, node)


async def _write_entitlement(db: AsyncSession, employee: Employee, actor: Employee) -> None:
    """R9: a start in the current year is pro-rated (Annual and Sick); an earlier start gets the
    normal entitlement. A future start is refused before this point (A-8)."""
    year = _today_year()
    for code, allowance in ALLOWANCE.items():
        if employee.start_date.year == year:
            kind, days = "prorata", prorata(employee.start_date, allowance)
        else:
            kind, days = "entitlement", allowance
        if days <= 0:
            continue
        await ledger.add_entry(
            db,
            employee_id=employee.id,
            leave_type_code=code,
            leave_year=year,
            kind=kind,
            days=days,
            source="hr",
            idempotency_key=f"{kind}:{year}:{employee.id}:{code}",
            created_by=actor.id,
        )


async def list_page(
    db: AsyncSession, actor: Employee, limit: int, cursor: str | None
) -> tuple[list[Employee], str | None]:
    _require_hr(actor)
    offset = decode_cursor(cursor)
    rows = await repository.list_page(db, offset, limit + 1)
    more = len(rows) > limit
    return rows[:limit], encode_cursor(offset + limit) if more else None


async def get(db: AsyncSession, actor: Employee, employee_id: uuid.UUID) -> Employee:
    _require_hr(actor)
    return await _get(db, employee_id)


async def create(
    db: AsyncSession, actor: Employee, body: EmployeeCreate, ip: str | None
) -> Employee:
    _require_hr(actor)
    try:
        auth.require_company_email(body.email)  # R1, also enforced by the DB CHECK
    except auth.InvalidEmailDomain as exc:
        raise ProblemError(422, str(exc)) from exc
    if body.start_date.year > _today_year():
        raise ProblemError(422, "Start date cannot be in a future year.")
    if await repository.get_by_email(db, body.email) is not None:
        raise ProblemError(409, DUPLICATE)
    await repository.lock_manager_graph(db)
    await _check_team(db, body.team_id)
    await _check_manager(db, body.manager_id, None)
    employee = Employee(
        name=body.name,
        email=body.email,
        role=body.role,
        team_id=body.team_id,
        manager_id=body.manager_id,
        start_date=body.start_date,
    )
    try:
        await repository.add(db, employee)
    except IntegrityError as exc:  # concurrent insert of the same email
        await db.rollback()
        raise ProblemError(409, DUPLICATE) from exc
    await _write_entitlement(db, employee, actor)
    await auth.issue_invite(db, employee)  # R3: queues the email; the link is never returned
    await audit.record(
        db,
        actor_id=actor.id,
        action="employee.create",
        target_type=TARGET,
        target_id=str(employee.id),
        detail={"after": _snapshot(employee)},
        ip=ip,
    )
    await db.commit()
    return employee


async def update(
    db: AsyncSession, actor: Employee, employee_id: uuid.UUID, body: EmployeePatch, ip: str | None
) -> Employee:
    _require_hr(actor)
    await repository.lock_manager_graph(db)
    employee = await _get(db, employee_id)
    before = _snapshot(employee)
    changes = body.model_dump(exclude_unset=True)
    if "team_id" in changes:
        await _check_team(db, changes["team_id"])
    if "manager_id" in changes:
        await _check_manager(db, changes["manager_id"], employee.id)
    for field, value in changes.items():
        setattr(employee, field, value)
    employee.updated_at = func.now()
    await db.flush()
    after = _snapshot(employee)
    await audit.record(
        db,
        actor_id=actor.id,
        action="employee.role_change" if before["role"] != after["role"] else "employee.update",
        target_type=TARGET,
        target_id=str(employee.id),
        detail={"before": before, "after": after, "fields": sorted(changes)},
        ip=ip,
    )
    await db.commit()
    return employee


async def resend_invite(
    db: AsyncSession, actor: Employee, employee_id: uuid.UUID, ip: str | None
) -> None:
    _require_hr(actor)
    employee = await _get(db, employee_id)
    if not employee.is_active:
        raise ProblemError(409, "Employee is inactive.")
    await auth.issue_invite(db, employee, datetime.now(UTC))
    await audit.record(
        db,
        actor_id=actor.id,
        action="employee.invite_resent",
        target_type=TARGET,
        target_id=str(employee.id),
        ip=ip,
    )
    await db.commit()
