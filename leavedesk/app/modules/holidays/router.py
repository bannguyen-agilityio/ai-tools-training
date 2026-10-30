import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.router import client_ip
from app.modules.holidays import service
from app.modules.holidays.dependencies import HrUser, YearParam
from app.modules.holidays.schemas import (
    HolidayChangeOut,
    HolidayCreate,
    HolidayList,
    HolidayOut,
    HolidayPatch,
    ImpactOut,
)
from app.modules.identity.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["holidays"])
DB = Annotated[AsyncSession, Depends(get_db)]


def _changed(holiday: object, affected: int) -> HolidayChangeOut:
    return HolidayChangeOut(holiday=HolidayOut.model_validate(holiday), affected_requests=affected)


@router.get("/holidays", response_model=HolidayList)
async def list_holidays(_: CurrentUser, db: DB, year: YearParam) -> HolidayList:
    rows = await service.list_for_year(db, year)
    return HolidayList(items=[HolidayOut.model_validate(h) for h in rows])


@router.get("/hr/holidays/impact", response_model=ImpactOut)
async def holiday_impact(
    user: HrUser,
    db: DB,
    holiday_date: Annotated[date, Query(alias="date")],
    previous_date: date | None = None,
) -> ImpactOut:
    return ImpactOut(
        holiday_date=holiday_date,
        affected_requests=await service.impact(db, user, holiday_date, previous_date),
    )


@router.post("/hr/holidays", response_model=HolidayChangeOut, status_code=201)
async def create_holiday(
    body: HolidayCreate, request: Request, response: Response, user: HrUser, db: DB
) -> HolidayChangeOut:
    holiday, affected = await service.create(db, user, body, client_ip(request))
    response.headers["Location"] = f"/api/v1/hr/holidays/{holiday.id}"  # spec 6.1 Creates
    return _changed(holiday, affected)


@router.patch("/hr/holidays/{holiday_id}", response_model=HolidayChangeOut)
async def update_holiday(
    holiday_id: uuid.UUID, body: HolidayPatch, request: Request, user: HrUser, db: DB
) -> HolidayChangeOut:
    return _changed(*await service.update(db, user, holiday_id, body, client_ip(request)))


@router.delete("/hr/holidays/{holiday_id}", response_model=HolidayChangeOut)
async def delete_holiday(
    holiday_id: uuid.UUID, request: Request, user: HrUser, db: DB
) -> HolidayChangeOut:
    return _changed(*await service.delete(db, user, holiday_id, client_ip(request)))
