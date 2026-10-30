import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.calendar import service
from app.modules.calendar.schemas import CalendarOut
from app.modules.identity.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["calendar"])
DB = Annotated[AsyncSession, Depends(get_db)]
Month = Annotated[str, Query(pattern=r"^(19|20)\d{2}-(0[1-9]|1[0-2])$")]


@router.get("/calendar", response_model=CalendarOut)
async def get_calendar(
    user: CurrentUser, db: DB, month: Month, team_id: uuid.UUID | None = None
) -> CalendarOut:
    return await service.month_view(db, user, month, team_id)
