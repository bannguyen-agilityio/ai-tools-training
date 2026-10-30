"""Deactivate an employee (R4, spec 5.5): one transaction, all or nothing.

Sets `is_active=false`, deletes sessions, cancels every Pending request (day rows inactive,
audited, approvers told). History stays. A-11: HR admins and the deputy are refused.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.auth import repository as auth_repository
from app.modules.email.privacy import RequestRef
from app.modules.email.templates import Event
from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest, LeaveRequestDay
from app.modules.notifications.service import emit
from app.modules.requests.cancel import approvers

CANCEL_REASON = "Account deactivated"  # the schema requires one when someone else cancels


async def deactivate(
    db: AsyncSession, actor: Employee, employee_id: uuid.UUID, ip: str | None
) -> Employee:
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")
    # Same lock as submit, so a request cannot slip in while the Pending ones are cancelled.
    employee = await db.scalar(select(Employee).where(Employee.id == employee_id).with_for_update())
    if employee is None:
        raise ProblemError(404, "Employee not found")
    if employee.id == actor.id:
        raise ProblemError(422, "You cannot deactivate yourself.")
    if employee.role == "hr" or employee.is_hr_deputy:
        raise ProblemError(
            422,
            "HR admins and the deputy cannot be deactivated yet.",
            code="DEACTIVATION_UNAVAILABLE",
        )
    if not employee.is_active:
        raise ProblemError(409, "This employee is already deactivated.")

    employee.is_active = False
    employee.deactivated_at = func.now()
    employee.updated_at = func.now()
    await db.flush()
    await auth_repository.delete_sessions(db, employee.id)

    pending = list(
        await db.scalars(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee.id, LeaveRequest.status == "pending")
            .with_for_update()
        )
    )
    for req in pending:
        await db.execute(
            update(LeaveRequest)
            .where(LeaveRequest.id == req.id)
            .values(
                status="cancelled",
                version=LeaveRequest.version + 1,
                cancelled_by=actor.id,
                cancel_reason=CANCEL_REASON,
                cancelled_at=func.now(),
                updated_at=func.now(),
            )
            .execution_options(synchronize_session=False)
        )
        await db.execute(
            update(LeaveRequestDay)
            .where(LeaveRequestDay.request_id == req.id)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
        )
        await audit.record(
            db,
            actor_id=actor.id,
            action="request.cancel",
            target_type="leave_request",
            target_id=str(req.id),
            detail={"request_id": str(req.id), "status": "cancelled"},
            ip=ip,
        )
        ref = RequestRef(req.id, employee.id, employee.name, req.start_date, req.end_date)
        for recipient in await approvers(db, req, employee):
            await emit(db, Event.REQUEST_CANCELLED_ON_DEACTIVATION, recipient, ref=ref)
    await audit.record(
        db,
        actor_id=actor.id,
        action="employee.deactivate",
        target_type="employee",
        target_id=str(employee.id),
        detail={"employee_id": str(employee.id), "count": len(pending)},
        ip=ip,
    )
    await db.commit()
    await db.refresh(employee)
    return employee
