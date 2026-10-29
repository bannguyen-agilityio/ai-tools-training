import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.email import outbox_service
from app.modules.email.schemas import OutboxEntryOut
from app.modules.identity.dependencies import require_hr
from app.modules.identity.models import Employee

router = APIRouter(prefix="/api/v1/hr/email-outbox", tags=["email"])


@router.get("", response_model=list[OutboxEntryOut])
async def list_outbox(
    _: Annotated[Employee, Depends(require_hr)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[Literal["failed"], Query()] = "failed",
) -> list[OutboxEntryOut]:
    return [OutboxEntryOut.model_validate(r) for r in await outbox_service.list_failed(db)]


@router.post("/{outbox_id}/retry", response_model=OutboxEntryOut)
async def retry_email(
    outbox_id: uuid.UUID,
    hr: Annotated[Employee, Depends(require_hr)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OutboxEntryOut:
    row = await outbox_service.retry(db, actor_id=hr.id, outbox_id=outbox_id)
    return OutboxEntryOut.model_validate(row)
