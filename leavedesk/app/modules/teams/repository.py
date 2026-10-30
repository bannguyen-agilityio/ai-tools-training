import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Employee, Team


async def list_all(db: AsyncSession) -> list[Team]:
    return list(await db.scalars(select(Team).order_by(Team.name, Team.id)))


async def get(db: AsyncSession, team_id: uuid.UUID) -> Team | None:
    return await db.get(Team, team_id)


async def get_employee(db: AsyncSession, employee_id: uuid.UUID) -> Employee | None:
    return await db.get(Employee, employee_id)


async def add(db: AsyncSession, team: Team) -> Team:
    db.add(team)
    await db.flush()
    return team
