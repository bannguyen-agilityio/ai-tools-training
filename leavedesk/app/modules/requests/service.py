import base64
import binascii
import uuid
from datetime import UTC, date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.email.privacy import RequestRef
from app.modules.email.templates import Event
from app.modules.identity.models import Employee
from app.modules.leave_days.models import LeaveRequest
from app.modules.notifications.service import emit
from app.modules.requests import repository, rules
from app.modules.requests.redaction import can_view, redact
from app.modules.requests.routing import Route, route_for
from app.modules.requests.schemas import (
    PreviewOut,
    RequestIn,
    RequestList,
    RequestOut,
    RuleIssue,
    YearBalance,
)

OVERLAP_RACE = "This overlaps your existing leave."


def _issue(err: ProblemError) -> RuleIssue:
    field_name = err.details[0]["field"] if err.details else None
    return RuleIssue(code=err.code or "INVALID", field=field_name, message=err.detail or "")


async def _evaluate(
    db: AsyncSession, user: Employee, body: RequestIn, today: date
) -> tuple[rules.Evaluation, Route | None]:
    """Rules plus routing. Routing is only worth checking once the request itself is valid."""
    ev = await rules.evaluate(db, user, body, today)
    route: Route | None = None
    try:
        route = await route_for(db, user)
    except ProblemError as exc:
        ev.errors.append(exc)
    return ev, route


async def preview(db: AsyncSession, user: Employee, body: RequestIn, today: date) -> PreviewOut:
    """Same pipeline as submit; writes nothing (spec 6.2 #9)."""
    ev, _ = await _evaluate(db, user, body, today)
    before = ev.available_before
    return PreviewOut(
        valid=not ev.errors,
        working_days=float(ev.working_days) if ev.working_days is not None else None,
        per_year=[
            YearBalance(
                year=year,
                days=float(days),
                available_before=float(before[year]) if before is not None else None,
                available_after=float(before[year] - days) if before is not None else None,
            )
            for year, days in sorted(ev.per_year.items())
        ],
        errors=[_issue(e) for e in ev.errors],
    )


async def create(
    db: AsyncSession, user: Employee, body: RequestIn, today: date, ip: str | None = None
) -> LeaveRequest:
    """Submit (R12, R13, R17; spec 5.5): lock the employee, run the rules, insert, audit, emit."""
    await repository.lock_employee(db, user.id)
    ev, route = await _evaluate(db, user, body, today)
    if ev.errors:
        raise ev.errors[0]
    assert route is not None  # a routing failure is in ev.errors
    working_days = ev.working_days
    assert working_days is not None

    req = LeaveRequest(
        id=uuid.uuid4(),
        employee_id=user.id,
        leave_type_code=body.leave_type,
        start_date=body.start_date,
        start_part=body.start_part,
        end_date=body.end_date,
        end_part=body.end_part,
        working_days=working_days,
        note=body.note,
        status="pending",
        queue=route.queue,
        assigned_to=route.assigned_to.id if route.assigned_to else None,
        submitted_at=datetime.now(UTC),
        notice_warning=False,
        version=1,
    )
    repository.add(db, req, ev.rows)
    try:
        await db.flush()
    except IntegrityError as exc:
        # The partial unique index is the backstop if the pre-check missed a concurrent insert.
        await db.rollback()
        raise ProblemError(
            409,
            OVERLAP_RACE,
            code="OVERLAP",
            details=[{"field": "start_date", "issue": OVERLAP_RACE}],
        ) from exc

    # Detail has ids and quantities only: never the type or the note (R30, §8).
    await audit.record(
        db,
        actor_id=user.id,
        action="request.create",
        target_type="leave_request",
        target_id=str(req.id),
        detail={"request_id": str(req.id), "status": "pending", "days": float(working_days)},
        ip=ip,
    )
    ref = RequestRef(req.id, user.id, user.name, req.start_date, req.end_date)
    for recipient in route.recipients:
        await emit(db, Event.REQUEST_CREATED, recipient, ref=ref)
    await db.commit()
    return req


async def get(db: AsyncSession, viewer: Employee, request_id: uuid.UUID) -> RequestOut:
    req = await repository.get(db, request_id)
    if req is None:
        raise ProblemError(404, "Request not found")
    if not can_view(viewer, req):
        raise ProblemError(403, "Not allowed")
    return redact(viewer, req)


def _decode_cursor(cursor: str | None) -> tuple[date, uuid.UUID] | None:
    """Keyset cursor `start_date|id`, so rows created between pages cannot shift a page."""
    if not cursor:
        return None
    try:
        start, last_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return date.fromisoformat(start), uuid.UUID(last_id)
    except (ValueError, binascii.Error) as exc:
        raise ProblemError(422, "Invalid cursor") from exc


def _encode_cursor(req: LeaveRequest) -> str:
    return base64.urlsafe_b64encode(f"{req.start_date.isoformat()}|{req.id}".encode()).decode()


async def list_own(
    db: AsyncSession,
    user: Employee,
    status: str | None,
    year: int | None,
    limit: int,
    cursor: str | None,
) -> RequestList:
    after = _decode_cursor(cursor)
    rows = await repository.list_own(db, user.id, status, year, after, limit + 1)
    page = rows[:limit]
    next_cursor = _encode_cursor(page[-1]) if len(rows) > limit else None
    return RequestList(items=[redact(user, r) for r in page], next_cursor=next_cursor)
