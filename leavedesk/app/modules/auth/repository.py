import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import UserIdentity
from app.modules.identity.models import Employee, Session


async def employee_by_email(db: AsyncSession, email: str) -> Employee | None:
    return await db.scalar(select(Employee).where(Employee.email == email.strip()))


async def password_identity(db: AsyncSession, employee_id: uuid.UUID) -> UserIdentity | None:
    return await db.scalar(
        select(UserIdentity).where(
            UserIdentity.employee_id == employee_id, UserIdentity.provider == "password"
        )
    )


async def delete_sessions(
    db: AsyncSession, employee_id: uuid.UUID, *, keep_token_hash: str | None = None
) -> None:
    stmt = delete(Session).where(Session.employee_id == employee_id)
    if keep_token_hash is not None:
        stmt = stmt.where(Session.token_hash != keep_token_hash)
    await db.execute(stmt)


async def delete_session_by_hash(db: AsyncSession, token_hash: str) -> None:
    await db.execute(delete(Session).where(Session.token_hash == token_hash))
