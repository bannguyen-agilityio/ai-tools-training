import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.approvals import repository
from app.modules.approvals.authz import can_decide
from app.modules.approvals.schemas import ApprovalList
from app.modules.audit import service as audit
from app.modules.email.privacy import RequestRef
from app.modules.email.templates import Event
from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest
from app.modules.notifications.service import emit
from app.modules.requests import repository as requests_repo
from app.modules.requests.redaction import redact
from app.modules.requests.schemas import RequestOut

ALREADY_DECIDED = "This request was already decided."


async def list_assigned(db: AsyncSession, actor: Employee) -> ApprovalList:
    rows = await repository.pending_for(db, actor)
    return ApprovalList(items=[redact(actor, r) for r in rows])


async def list_cover(db: AsyncSession, actor: Employee) -> ApprovalList:
    """The "On behalf of" tab (R20): managers only; the default list never includes these."""
    if actor.role != "manager":
        raise ProblemError(403, "Not allowed")
    rows = await repository.pending_cover(db, actor)
    return ApprovalList(items=[redact(actor, r) for r in rows])


async def _authorise(
    db: AsyncSession,
    actor: Employee,
    request_id: uuid.UUID,
    action: str,
    ip: str | None,
    on_behalf_of: uuid.UUID | None,
) -> LeaveRequest:
    req = await requests_repo.get(db, request_id)
    if req is None:
        raise ProblemError(404, "Request not found")
    if not can_decide(actor, req, on_behalf_of):
        # Committed before raising, so the refused attempt survives the error response (R22).
        await audit.record(
            db,
            actor_id=actor.id,
            action=f"{action}_denied",
            target_type="leave_request",
            target_id=str(req.id),
            detail={"request_id": str(req.id)},
            ip=ip,
        )
        await db.commit()
        raise ProblemError(403, "Not allowed")
    return req


async def _decide(
    db: AsyncSession,
    actor: Employee,
    request_id: uuid.UUID,
    version: int,
    *,
    action: str,
    status: str,
    event: Event,
    cover_event: Event,
    reason: str | None,
    ip: str | None,
    on_behalf_of: uuid.UUID | None,
) -> RequestOut:
    req = await _authorise(db, actor, request_id, action, ip, on_behalf_of)
    # Cover only when the manager-queue cover branch of can_decide authorised it: an assigned
    # manager or an HR approver never records (or emails) a stand-in relationship.
    is_cover = req.queue == "manager" and req.assigned_to != actor.id
    cover = req.assigned_to if is_cover else None
    owner = await db.get(Employee, req.employee_id)
    assert owner is not None  # FK
    decided = await repository.decide(
        db,
        request_id,
        version,
        status=status,
        actor_id=actor.id,
        reason=reason,
        on_behalf_of=cover,
    )
    if decided is None:
        await db.rollback()
        raise ProblemError(409, ALREADY_DECIDED, code="ALREADY_DECIDED")
    if status == "rejected":
        await repository.release_days(db, request_id)
    # Ids and quantities only: never the type, note or reason (R30, §8).
    await audit.record(
        db,
        actor_id=actor.id,
        action=f"request.{action}",
        target_type="leave_request",
        target_id=str(request_id),
        detail={"request_id": str(request_id), "status": status, "version": decided.version},
        acting_for_id=cover,
        ip=ip,
    )
    ref = RequestRef(decided.id, owner.id, owner.name, decided.start_date, decided.end_date)
    await emit(db, event, owner, ref=ref, rejection_reason=reason)
    if cover is not None:
        # The direct manager learns of it; no type, note or reason in the message.
        direct = await db.get(Employee, cover)
        assert direct is not None  # FK
        await emit(db, cover_event, direct, ref=ref, actor=actor)
    await db.commit()
    return redact(actor, decided)


async def approve(
    db: AsyncSession,
    actor: Employee,
    request_id: uuid.UUID,
    version: int,
    ip: str | None = None,
    on_behalf_of: uuid.UUID | None = None,
) -> RequestOut:
    """Pending -> Approved: reserved days become used; the day rows stay active (R18)."""
    return await _decide(
        db,
        actor,
        request_id,
        version,
        action="approve",
        status="approved",
        event=Event.REQUEST_APPROVED,
        cover_event=Event.REQUEST_APPROVED_ON_BEHALF,
        reason=None,
        ip=ip,
        on_behalf_of=on_behalf_of,
    )


async def reject(
    db: AsyncSession,
    actor: Employee,
    request_id: uuid.UUID,
    version: int,
    reason: str,
    ip: str | None = None,
    on_behalf_of: uuid.UUID | None = None,
) -> RequestOut:
    """Pending -> Rejected with a reason; the days are released (R19)."""
    return await _decide(
        db,
        actor,
        request_id,
        version,
        action="reject",
        status="rejected",
        event=Event.REQUEST_REJECTED,
        cover_event=Event.REQUEST_REJECTED_ON_BEHALF,
        reason=reason,
        ip=ip,
        on_behalf_of=on_behalf_of,
    )
