import uuid
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.holidays import repository
from app.modules.holidays.models import PublicHoliday
from app.modules.holidays.schemas import HolidayCreate, HolidayPatch
from app.modules.identity.models import Employee

MIN_YEAR, MAX_YEAR = 2000, 2100
ACTION_TARGET = "public_holiday"


def _require_hr(actor: Employee) -> None:
    # Defence in depth: the route dependency already requires HR; the deputy has no admin rights.
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")


def _snapshot(holiday: PublicHoliday) -> dict[str, Any]:
    return {"holiday_date": holiday.holiday_date.isoformat(), "name": holiday.name}


def _check_year(holiday_date: date) -> None:
    if not MIN_YEAR <= holiday_date.year <= MAX_YEAR:
        raise ProblemError(422, "Holiday date is out of range")


async def _duplicate_check(db: AsyncSession, holiday_date: date, own_id: uuid.UUID | None) -> None:
    existing = await repository.get_by_date(db, holiday_date)
    if existing is not None and existing.id != own_id:
        raise ProblemError(409, "There is already a holiday on that date.")


async def _get(db: AsyncSession, holiday_id: uuid.UUID) -> PublicHoliday:
    holiday = await repository.get(db, holiday_id)
    if holiday is None:
        raise ProblemError(404, "Holiday not found")
    return holiday


async def list_for_year(db: AsyncSession, year: int) -> list[PublicHoliday]:
    return await repository.list_year(db, year)


async def impact(
    db: AsyncSession, actor: Employee, holiday_date: date, previous_date: date | None = None
) -> int:
    """Requests touched by a holiday on `holiday_date`; when an existing holiday moves, also
    those on `previous_date`, matching the count the edit itself returns."""
    _require_hr(actor)
    dates = {holiday_date} if previous_date is None else {holiday_date, previous_date}
    return await repository.count_affected(db, dates)


async def create(
    db: AsyncSession, actor: Employee, body: HolidayCreate, ip: str | None
) -> tuple[PublicHoliday, int]:
    _require_hr(actor)
    _check_year(body.holiday_date)
    await _duplicate_check(db, body.holiday_date, None)
    holiday = PublicHoliday(
        holiday_date=body.holiday_date, name=body.name, source="manual", created_by=actor.id
    )
    try:
        await repository.add(db, holiday)
    except IntegrityError as exc:  # concurrent insert of the same date
        await db.rollback()
        raise ProblemError(409, "There is already a holiday on that date.") from exc
    affected = await repository.count_affected(db, [holiday.holiday_date])
    await audit.record(
        db,
        actor_id=actor.id,
        action="holiday.create",
        target_type=ACTION_TARGET,
        target_id=str(holiday.id),
        detail={"after": _snapshot(holiday), "count": affected},
        ip=ip,
    )
    await db.commit()
    return holiday, affected


async def update(
    db: AsyncSession, actor: Employee, holiday_id: uuid.UUID, body: HolidayPatch, ip: str | None
) -> tuple[PublicHoliday, int]:
    _require_hr(actor)
    holiday = await _get(db, holiday_id)
    before = _snapshot(holiday)
    old_date = holiday.holiday_date
    if (body.holiday_date in (None, old_date)) and (body.name in (None, holiday.name)):
        return holiday, await repository.count_affected(db, [old_date])  # nothing to change
    if body.holiday_date is not None:
        _check_year(body.holiday_date)
        await _duplicate_check(db, body.holiday_date, holiday.id)
        holiday.holiday_date = body.holiday_date
    if body.name is not None:
        holiday.name = body.name
    holiday.source = "manual"
    holiday.updated_at = func.now()
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ProblemError(409, "There is already a holiday on that date.") from exc
    # The old and the new date both change what counts as a working day.
    affected = await repository.count_affected(db, {old_date, holiday.holiday_date})
    await audit.record(
        db,
        actor_id=actor.id,
        action="holiday.update",
        target_type=ACTION_TARGET,
        target_id=str(holiday.id),
        detail={"before": before, "after": _snapshot(holiday), "count": affected},
        ip=ip,
    )
    await db.commit()
    return holiday, affected


async def delete(
    db: AsyncSession, actor: Employee, holiday_id: uuid.UUID, ip: str | None
) -> tuple[PublicHoliday, int]:
    _require_hr(actor)
    holiday = await _get(db, holiday_id)
    before = _snapshot(holiday)
    affected = await repository.count_affected(db, [holiday.holiday_date])
    if not await repository.remove(db, holiday.id):
        raise ProblemError(404, "Holiday not found")
    await audit.record(
        db,
        actor_id=actor.id,
        action="holiday.delete",
        target_type=ACTION_TARGET,
        target_id=str(holiday.id),
        detail={"before": before, "count": affected},
        ip=ip,
    )
    await db.commit()
    return holiday, affected
