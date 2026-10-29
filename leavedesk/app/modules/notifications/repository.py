import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification


async def get(db: AsyncSession, notification_id: uuid.UUID) -> Notification | None:
    return await db.get(Notification, notification_id)


async def list_for(
    db: AsyncSession, employee_id: uuid.UUID, *, unread_only: bool, limit: int
) -> list[Notification]:
    stmt = select(Notification).where(Notification.employee_id == employee_id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    result = await db.scalars(stmt.order_by(Notification.created_at.desc()).limit(limit))
    return list(result)


async def unread_count(db: AsyncSession, employee_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.employee_id == employee_id, Notification.read_at.is_(None))
        )
        or 0
    )


async def mark_all_read(db: AsyncSession, employee_id: uuid.UUID, now: datetime) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.employee_id == employee_id, Notification.read_at.is_(None))
        .values(read_at=now)
    )
