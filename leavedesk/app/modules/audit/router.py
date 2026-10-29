from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.audit import repository
from app.modules.audit.schemas import AuditEntryOut
from app.modules.identity.dependencies import require_hr
from app.modules.identity.models import Employee

router = APIRouter(prefix="/api/v1/audit-log", tags=["audit"])


@router.get("", response_model=list[AuditEntryOut])
def list_audit_log(
    _: Annotated[Employee, Depends(require_hr)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditEntryOut]:
    return [AuditEntryOut.model_validate(e) for e in repository.list_recent(db, limit)]
