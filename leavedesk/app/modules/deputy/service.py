"""Assign the one deputy HR admin (R36, spec 6.2 #22).

The deputy keeps their own role and gains only approval and cover rights. At most one at a
time: the old deputy is cleared and the new one set in one transaction; the partial unique
index is the backstop for two HR admins assigning at once.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.deputy.schemas import DeputyOut
from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest

DEPUTY_LOCK = 36  # advisory lock key: assignments are serialised (R36)


def _require_hr(actor: Employee) -> None:
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")


async def _current(db: AsyncSession) -> Employee | None:
    return await db.scalar(select(Employee).where(Employee.is_hr_deputy, Employee.is_active))


def _out(deputy: Employee | None) -> DeputyOut:
    if deputy is None:
        return DeputyOut(employee_id=None)
    return DeputyOut(employee_id=deputy.id, name=deputy.name, email=deputy.email)


async def get(db: AsyncSession, actor: Employee) -> DeputyOut:
    _require_hr(actor)
    return _out(await _current(db))


async def assign(
    db: AsyncSession, actor: Employee, employee_id: uuid.UUID | None, ip: str | None
) -> DeputyOut:
    _require_hr(actor)
    new: Employee | None = None
    if employee_id is not None:
        new = await db.get(Employee, employee_id)
        if new is None or not new.is_active:
            raise ProblemError(422, "The deputy must be an active employee.")
        if new.role == "hr":
            raise ProblemError(422, "An HR admin cannot also be the deputy.")
    await db.execute(select(func.pg_advisory_xact_lock(DEPUTY_LOCK)))
    old = await _current(db)
    if (old.id if old else None) == employee_id:
        return _out(old)
    if new is None and old is not None:
        # An HR admin's own leave is decided only by the deputy; clearing would strand it.
        open_items = await db.scalar(
            select(func.count())
            .select_from(LeaveRequest)
            .where(LeaveRequest.queue == "deputy", LeaveRequest.status == "pending")
        )
        if open_items:
            raise ProblemError(
                409,
                "HR leave is waiting for the deputy. Replace the deputy or decide it first.",
                code="DEPUTY_HAS_PENDING",
            )
    try:
        # Includes inactive leftovers, so a deactivated deputy never blocks the unique index.
        await db.execute(
            update(Employee)
            .where(Employee.is_hr_deputy)
            .values(is_hr_deputy=False)
            .execution_options(synchronize_session=False)
        )
        if new is not None:
            await db.execute(
                update(Employee)
                .where(Employee.id == new.id)
                .values(is_hr_deputy=True)
                .execution_options(synchronize_session=False)
            )
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ProblemError(409, "The deputy was changed by someone else; reload.") from exc
    await audit.record(
        db,
        actor_id=actor.id,
        action="employee.role_change",
        target_type="employee",
        target_id=str(new.id if new else old.id if old else actor.id),
        detail={
            "before": {"deputy_id": str(old.id) if old else None},
            "after": {"deputy_id": str(new.id) if new else None},
            "fields": ["is_hr_deputy"],
        },
        ip=ip,
    )
    await db.commit()
    if new is not None:
        await db.refresh(new)
    return _out(new)
