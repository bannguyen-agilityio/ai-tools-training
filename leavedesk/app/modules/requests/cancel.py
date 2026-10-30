"""Cancel a request: the owner while Pending (R16), HR once Approved (R21).

One guarded UPDATE decides the race with approve/reject and with a second cancel: whoever
matches `version` and the expected status wins, the other gets 409 (spec 5.5). Days are
refunded by derivation (day rows go inactive), so a second cancel cannot refund twice.
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
    """Who was asked to decide: the assigned manager or deputy, or every HR approver (A-14)."""
    if req.queue in ("manager", "deputy") and req.assigned_to is not None:
        manager = await db.get(Employee, req.assigned_to)
        return [manager] if manager is not None and manager.is_active else []
    return await hr_approvers(db, owner)


async def _cancel_guarded(
    db: AsyncSession, request_id: uuid.UUID, version: int, expected: str, **values: object
) -> None:
    """The one guarded UPDATE: only a row at `version` and `expected` status is cancelled, and its
    day rows go inactive (the refund). Anyone who lost the race gets 409."""
    won = await db.scalar(
        update(LeaveRequest)
        .where(
            LeaveRequest.id == request_id,
            LeaveRequest.version == version,
            LeaveRequest.status == expected,
        )
        .values(
            status="cancelled",
            version=LeaveRequest.version + 1,
            cancelled_at=func.now(),
            updated_at=func.now(),
            **values,
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

    await _cancel_guarded(db, req.id, version, "pending", cancelled_by=user.id)
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


async def cancel(
    db: AsyncSession,
    user: Employee,
    request_id: uuid.UUID,
    version: int,
    reason: str | None,
    ip: str | None = None,
) -> LeaveRequest:
    """Owner path first; anyone else must be an HR admin (the deputy is excluded, R36)."""
    req = await repository.get(db, request_id)
    if req is None:
        raise ProblemError(404, "Request not found")
    if req.employee_id == user.id:
        return await cancel_own(db, user, request_id, version, ip)
    if user.role != "hr":
        raise ProblemError(403, "Only the owner or HR can cancel this request.")
    if req.status != "approved":
        raise ProblemError(403, "HR can only cancel an Approved request.", code="NOT_APPROVED")
    if reason is None:
        raise ProblemError(422, "A reason is required to cancel someone's leave.")
    return await cancel_by_hr(db, user, req, version, reason, ip)


async def cancel_by_hr(
    db: AsyncSession,
    hr: Employee,
    req: LeaveRequest,
    version: int,
    reason: str,
    ip: str | None,
) -> LeaveRequest:
    await _cancel_guarded(db, req.id, version, "approved", cancelled_by=hr.id, cancel_reason=reason)
    await db.refresh(req)
    owner = await db.get(Employee, req.employee_id)
    assert owner is not None

    # Actor and ids only: the reason is HR free text and stays out of audit and email (R30, §8).
    await audit.record(
        db,
        actor_id=hr.id,
        action="request.cancel",
        target_type="leave_request",
        target_id=str(req.id),
        detail={"request_id": str(req.id), "status": "cancelled"},
        ip=ip,
    )
    ref = RequestRef(req.id, owner.id, owner.name, req.start_date, req.end_date)
    recipients = [owner, *(a for a in await approvers(db, req, owner) if a.id != hr.id)]
    for recipient in recipients:
        await emit(db, Event.REQUEST_CANCELLED_BY_HR, recipient, ref=ref)
    await db.commit()
    return req
