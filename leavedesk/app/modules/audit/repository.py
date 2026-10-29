from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


async def add(db: AsyncSession, entry: AuditLog) -> AuditLog:
    db.add(entry)
    await db.flush()
    return entry


async def list_recent(db: AsyncSession, limit: int) -> list[AuditLog]:
    result = await db.scalars(select(AuditLog).order_by(AuditLog.at.desc()).limit(limit))
    return list(result)
