import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.router import client_ip
from app.modules.balances import hr_service as service
from app.modules.balances.hr_schemas import (
    BalanceList,
    EmployeeBalances,
    EntryIn,
    EntryOut,
    Summary,
)
from app.modules.employees.dependencies import HrUser

router = APIRouter(prefix="/api/v1/hr", tags=["balances"])
DB = Annotated[AsyncSession, Depends(get_db)]
Year = Annotated[int | None, Query(ge=2000, le=2100)]


@router.get("/balances", response_model=BalanceList)
async def list_balances(user: HrUser, db: DB, year: Year = None) -> BalanceList:
    return await service.all_balances(db, user, year)


@router.get("/employees/{employee_id}/balances", response_model=EmployeeBalances)
async def employee_balances(
    employee_id: uuid.UUID, user: HrUser, db: DB, year: Year = None
) -> EmployeeBalances:
    return await service.employee_balances(db, user, employee_id, year)


@router.post("/employees/{employee_id}/balance-entries/preview", response_model=Summary)
async def preview_entry(employee_id: uuid.UUID, body: EntryIn, user: HrUser, db: DB) -> Summary:
    return await service.preview(db, user, employee_id, body)


@router.post("/employees/{employee_id}/balance-entries", response_model=EntryOut, status_code=201)
async def create_entry(
    employee_id: uuid.UUID,
    body: EntryIn,
    request: Request,
    response: Response,
    user: HrUser,
    db: DB,
) -> EntryOut:
    entry = await service.create(db, user, employee_id, body, client_ip(request))
    response.headers["Location"] = f"/api/v1/hr/employees/{employee_id}/balances"
    return EntryOut.model_validate(entry)
