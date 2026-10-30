import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.router import client_ip
from app.modules.employees import service
from app.modules.employees.dependencies import HrUser
from app.modules.employees.schemas import (
    EmployeeCreate,
    EmployeeList,
    EmployeeOut,
    EmployeePatch,
)

router = APIRouter(prefix="/api/v1/hr/employees", tags=["employees"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=EmployeeList)
async def list_employees(
    user: HrUser,
    db: DB,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> EmployeeList:
    rows, next_cursor = await service.list_page(db, user, limit, cursor)
    return EmployeeList(
        items=[EmployeeOut.model_validate(r) for r in rows], next_cursor=next_cursor
    )


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: uuid.UUID, user: HrUser, db: DB) -> EmployeeOut:
    return EmployeeOut.model_validate(await service.get(db, user, employee_id))


@router.post("", response_model=EmployeeOut, status_code=201)
async def create_employee(
    body: EmployeeCreate, request: Request, response: Response, user: HrUser, db: DB
) -> EmployeeOut:
    employee = await service.create(db, user, body, client_ip(request))
    response.headers["Location"] = f"/api/v1/hr/employees/{employee.id}"
    return EmployeeOut.model_validate(employee)


@router.patch("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: uuid.UUID, body: EmployeePatch, request: Request, user: HrUser, db: DB
) -> EmployeeOut:
    employee = await service.update(db, user, employee_id, body, client_ip(request))
    return EmployeeOut.model_validate(employee)


@router.post("/{employee_id}/invite", status_code=204)
async def resend_invite(employee_id: uuid.UUID, request: Request, user: HrUser, db: DB) -> None:
    await service.resend_invite(db, user, employee_id, client_ip(request))
