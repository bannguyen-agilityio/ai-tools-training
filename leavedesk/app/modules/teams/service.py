import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.identity.models import Employee, Team
from app.modules.teams import repository
from app.modules.teams.schemas import TeamCreate, TeamPatch

TARGET = "team"
DUPLICATE = "A team with that name already exists."


def _require_hr(actor: Employee) -> None:
    if actor.role != "hr":
        raise ProblemError(403, "Not allowed")


def _snapshot(team: Team) -> dict[str, Any]:
    return {"manager_id": str(team.manager_id) if team.manager_id else None}


async def _check_manager(db: AsyncSession, manager_id: uuid.UUID | None) -> None:
    if manager_id is None:
        return
    manager = await repository.get_employee(db, manager_id)
    if manager is None or not manager.is_active:
        raise ProblemError(422, "Manager must be an active employee.")


async def list_all(db: AsyncSession, actor: Employee) -> list[Team]:
    _require_hr(actor)
    return await repository.list_all(db)


async def create(db: AsyncSession, actor: Employee, body: TeamCreate, ip: str | None) -> Team:
    _require_hr(actor)
    await _check_manager(db, body.manager_id)
    team = Team(name=body.name, manager_id=body.manager_id)
    try:
        await repository.add(db, team)
    except IntegrityError as exc:
        await db.rollback()
        raise ProblemError(409, DUPLICATE) from exc
    await audit.record(
        db,
        actor_id=actor.id,
        action="team.create",
        target_type=TARGET,
        target_id=str(team.id),
        detail={"after": _snapshot(team)},
        ip=ip,
    )
    await db.commit()
    return team


async def update(
    db: AsyncSession, actor: Employee, team_id: uuid.UUID, body: TeamPatch, ip: str | None
) -> Team:
    _require_hr(actor)
    team = await repository.get(db, team_id)
    if team is None:
        raise ProblemError(404, "Team not found")
    before = _snapshot(team)
    changes = body.model_dump(exclude_unset=True)
    if "manager_id" in changes:
        await _check_manager(db, changes["manager_id"])
    for field, value in changes.items():
        setattr(team, field, value)
    team.updated_at = func.now()
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ProblemError(409, DUPLICATE) from exc
    await audit.record(
        db,
        actor_id=actor.id,
        action="team.update",
        target_type=TARGET,
        target_id=str(team.id),
        detail={"before": before, "after": _snapshot(team), "fields": sorted(changes)},
        ip=ip,
    )
    await db.commit()
    return team
