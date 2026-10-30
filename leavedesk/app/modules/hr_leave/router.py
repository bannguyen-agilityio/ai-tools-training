import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.employees.dependencies import HrUser
from app.modules.hr_leave import service
from app.modules.hr_leave.schemas import HrLeaveList, LeaveType, Status

router = APIRouter(prefix="/api/v1/hr", tags=["hr-leave"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/leave", response_model=HrLeaveList)
async def all_leave(
    user: HrUser,
    db: DB,
    status: Status = "approved",
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    employee_id: uuid.UUID | None = None,
    team_id: uuid.UUID | None = None,
    type: LeaveType | None = None,  # noqa: A002
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> HrLeaveList:
    return await service.list_leave(
        db,
        user,
        status=status,
        start=from_,
        end=to,
        employee_id=employee_id,
        team_id=team_id,
        leave_type=type,
        limit=limit,
        cursor=cursor,
    )
