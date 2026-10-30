"""Cancel a request (R16; HR's Approved path is plan 14/R21 and adds a branch here).

One guarded UPDATE decides the race with approve/reject: whoever matches `version` and
`status='pending'` wins, the other gets 409 (spec 5.5).
"""

import uuid

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.email.privacy import RequestRef
from app.modules.email.templates import Event
from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest, LeaveRequestDay
from app.modules.notifications.service import emit
from app.modules.requests import repository
from app.modules.requests.routing import hr_approvers

STALE = "This request was already decided or changed. Reload it."


async def approvers(db: AsyncSession, req: LeaveRequest, owner: Employee) -> list[Employee]:
    """Who was asked to decide: the assigned manager, or every HR approver (A-14)."""
    if req.queue == "manager" and req.assigned_to is not None:
        manager = await db.get(Employee, req.assigned_to)
        return [manager] if manager is not None and manager.is_active else []
    return await hr_approvers(db, owner)


async def cancel_own(
    db: AsyncSession,
    user: Employee,
    request_id: uuid.UUID,
    version: int,
    ip: str | None = None,
) -> LeaveRequest:
    req = await repository.get(db, request_id)
    if req is None:
        raise ProblemError(404, "Request not found")
    if req.employee_id != user.id:
        raise ProblemError(403, "Only the owner can cancel this request.")
    if req.status != "pending":
        raise ProblemError(403, "Only a Pending request can be cancelled.", code="NOT_PENDING")

    won = await db.scalar(
        update(LeaveRequest)
        .where(
            LeaveRequest.id == request_id,
            LeaveRequest.version == version,
            LeaveRequest.status == "pending",
        )
        .values(
            status="cancelled",
            version=LeaveRequest.version + 1,
            cancelled_by=user.id,
            cancelled_at=func.now(),
            updated_at=func.now(),
        )
        .returning(LeaveRequest.id)
        .execution_options(synchronize_session=False)
    )
    if won is None:
        await db.rollback()
        raise ProblemError(409, STALE, code="STALE_VERSION")
    await db.execute(
        update(LeaveRequestDay)
        .where(LeaveRequestDay.request_id == request_id)
        .values(is_active=False)
        .execution_options(synchronize_session=False)
    )
    await db.refresh(req)

    # Ids and quantities only: never the type or the note (R30, §8).
    await audit.record(
        db,
        actor_id=user.id,
        action="request.cancel",
        target_type="leave_request",
        target_id=str(req.id),
        detail={"request_id": str(req.id), "status": "cancelled"},
        ip=ip,
    )
    ref = RequestRef(req.id, user.id, user.name, req.start_date, req.end_date)
    for recipient in await approvers(db, req, user):
        await emit(db, Event.REQUEST_CANCELLED_BY_EMPLOYEE, recipient, ref=ref)
    await db.commit()
    return req
