import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest, LeaveRequestDay


async def pending_for(db: AsyncSession, actor: Employee) -> list[LeaveRequest]:
    """Pending items the actor may decide (spec 6.2 #13, scope=assigned), oldest first."""
    queues = [and_(LeaveRequest.queue == "manager", LeaveRequest.assigned_to == actor.id)]
    if actor.role == "hr" or actor.is_hr_deputy:
        queues.append(LeaveRequest.queue == "hr")
    if actor.is_hr_deputy:
        queues.append(LeaveRequest.queue == "deputy")
    result = await db.scalars(
        select(LeaveRequest)
        .where(
            LeaveRequest.status == "pending",
            LeaveRequest.employee_id != actor.id,
            or_(*queues),
        )
        .order_by(LeaveRequest.submitted_at, LeaveRequest.id)
    )
    return list(result)


async def decide(
    db: AsyncSession,
    request_id: uuid.UUID,
    version: int,
    *,
    status: str,
    actor_id: uuid.UUID,
    reason: str | None,
) -> LeaveRequest | None:
    """Guarded update: only a Pending row at `version` changes. None: someone got there first."""
    now = datetime.now(UTC)
    return await db.scalar(
        update(LeaveRequest)
        .where(
            LeaveRequest.id == request_id,
            LeaveRequest.status == "pending",
            LeaveRequest.version == version,
        )
        .values(
            status=status,
            decided_by=actor_id,
            decided_at=now,
            decision_reason=reason,
            version=LeaveRequest.version + 1,
            updated_at=now,
        )
        .returning(LeaveRequest)
        .execution_options(populate_existing=True)
    )


async def release_days(db: AsyncSession, request_id: uuid.UUID) -> None:
    await db.execute(
        update(LeaveRequestDay)
        .where(LeaveRequestDay.request_id == request_id)
        .values(is_active=False)
    )
