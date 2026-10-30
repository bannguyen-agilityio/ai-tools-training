import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.approvals import service
from app.modules.approvals.schemas import ApprovalList, ApproveIn, RejectIn
from app.modules.auth.router import client_ip
from app.modules.identity.dependencies import CurrentUser
from app.modules.requests.schemas import RequestOut

router = APIRouter(prefix="/api/v1", tags=["approvals"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/approvals", response_model=ApprovalList)
async def list_approvals(
    user: CurrentUser,
    db: DB,
    scope: Annotated[Literal["assigned", "cover"], Query()] = "assigned",
) -> ApprovalList:
    if scope == "cover":
        return await service.list_cover(db, user)
    return await service.list_assigned(db, user)


@router.post("/approvals/{request_id}/approve", response_model=RequestOut)
async def approve(
    request_id: uuid.UUID, body: ApproveIn, request: Request, user: CurrentUser, db: DB
) -> RequestOut:
    return await service.approve(
        db, user, request_id, body.version, client_ip(request), body.on_behalf_of
    )


@router.post("/approvals/{request_id}/reject", response_model=RequestOut)
async def reject(
    request_id: uuid.UUID, body: RejectIn, request: Request, user: CurrentUser, db: DB
) -> RequestOut:
    return await service.reject(
        db, user, request_id, body.version, body.reason, client_ip(request), body.on_behalf_of
    )
