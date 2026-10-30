from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.modules.balances import me_service
from app.modules.balances.schemas import MyBalances
from app.modules.identity.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1/me", tags=["balances"])


def get_today() -> date:
    return datetime.now(ZoneInfo(get_settings().company_tz)).date()  # overridable in tests


@router.get("/balances", response_model=MyBalances)
async def my_balances(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    today: Annotated[date, Depends(get_today)],
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> MyBalances:
    # No employee id is accepted: managers cannot see their reports' balances (Q11).
    return await me_service.my_balances(db, user, year or today.year, today)
