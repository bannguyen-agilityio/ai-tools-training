import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.router import client_ip
from app.modules.balances.me_router import get_today
from app.modules.identity.dependencies import CurrentUser
from app.modules.requests import service
from app.modules.requests.redaction import redact
from app.modules.requests.schemas import (
    PreviewOut,
    RequestIn,
    RequestList,
    RequestOut,
    Status,
)

router = APIRouter(prefix="/api/v1", tags=["requests"])
DB = Annotated[AsyncSession, Depends(get_db)]
Today = Annotated[date, Depends(get_today)]


@router.post("/requests/preview", response_model=PreviewOut)
async def preview_request(body: RequestIn, user: CurrentUser, db: DB, today: Today) -> PreviewOut:
    return await service.preview(db, user, body, today)


@router.post("/requests", response_model=RequestOut, status_code=201)
async def create_request(
    body: RequestIn,
    request: Request,
    response: Response,
    user: CurrentUser,
    db: DB,
    today: Today,
) -> RequestOut:
    req = await service.create(db, user, body, today, client_ip(request))
    response.headers["Location"] = f"/api/v1/requests/{req.id}"
    return redact(user, req)


@router.get("/requests/{request_id}", response_model=RequestOut)
async def get_request(request_id: uuid.UUID, user: CurrentUser, db: DB) -> RequestOut:
    return await service.get(db, user, request_id)


@router.get("/me/requests", response_model=RequestList)
async def my_requests(
    user: CurrentUser,
    db: DB,
    status: Status | None = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> RequestList:
    return await service.list_own(db, user, status, year, limit, cursor)
