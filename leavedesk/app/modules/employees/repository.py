import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Employee, Team

MANAGER_LOCK = 7_231_023  # serialises manager edits so two edits cannot close a loop


async def lock_manager_graph(db: AsyncSession) -> None:
    await db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": MANAGER_LOCK})


async def get(db: AsyncSession, employee_id: uuid.UUID) -> Employee | None:
    return await db.get(Employee, employee_id)


async def get_by_email(db: AsyncSession, email: str) -> Employee | None:
    return await db.scalar(select(Employee).where(Employee.email == email))


async def get_team(db: AsyncSession, team_id: uuid.UUID) -> Team | None:
    return await db.get(Team, team_id)


async def list_page(db: AsyncSession, offset: int, limit: int) -> list[Employee]:
    result = await db.scalars(
        select(Employee).order_by(Employee.name, Employee.id).offset(offset).limit(limit)
    )
    return list(result)


async def add(db: AsyncSession, employee: Employee) -> Employee:
    db.add(employee)
    await db.flush()
    return employee


async def manager_of(db: AsyncSession, employee_id: uuid.UUID) -> uuid.UUID | None:
    return await db.scalar(select(Employee.manager_id).where(Employee.id == employee_id))
