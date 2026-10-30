from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.router import client_ip
from app.modules.deputy import service
from app.modules.deputy.schemas import DeputyIn, DeputyOut
from app.modules.employees.dependencies import HrUser

router = APIRouter(prefix="/api/v1/hr/deputy", tags=["deputy"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=DeputyOut)
async def get_deputy(user: HrUser, db: DB) -> DeputyOut:
    return await service.get(db, user)


@router.put("", response_model=DeputyOut)
async def put_deputy(body: DeputyIn, request: Request, user: HrUser, db: DB) -> DeputyOut:
    return await service.assign(db, user, body.employee_id, client_ip(request))
