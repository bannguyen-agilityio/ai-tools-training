from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.router import client_ip
from app.modules.balances.me_router import get_today
from app.modules.employees.dependencies import HrUser
from app.modules.requests import service
from app.modules.requests.redaction import redact
from app.modules.requests.schemas import HrRequestIn, RequestOut

router = APIRouter(prefix="/api/v1/hr", tags=["requests"])
DB = Annotated[AsyncSession, Depends(get_db)]
Today = Annotated[date, Depends(get_today)]


@router.post("/requests", response_model=RequestOut, status_code=201)
async def enter_leave(
    body: HrRequestIn, request: Request, response: Response, user: HrUser, db: DB, today: Today
) -> RequestOut:
    req = await service.create_for(db, user, body, today, client_ip(request))
    response.headers["Location"] = f"/api/v1/requests/{req.id}"
    return redact(user, req)
