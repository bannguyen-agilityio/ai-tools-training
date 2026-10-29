import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.identity.dependencies import CurrentUser
from app.modules.notifications import repository, service
from app.modules.notifications.schemas import NotificationList, NotificationOut

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
async def list_notifications(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> NotificationList:
    rows = await repository.list_for(db, user.id, unread_only=unread_only, limit=limit)
    return NotificationList(
        unread_count=await repository.unread_count(db, user.id),
        items=[NotificationOut.model_validate(r) for r in rows],
    )


@router.post("/read-all", status_code=204)
async def read_all(user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]) -> Response:
    await repository.mark_all_read(db, user.id, datetime.now(UTC))
    await db.commit()
    return Response(status_code=204)


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def read_one(
    notification_id: uuid.UUID, user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
) -> NotificationOut:
    return NotificationOut.model_validate(await service.mark_read(db, user, notification_id))
