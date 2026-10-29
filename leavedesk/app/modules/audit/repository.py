from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def add(db: Session, entry: AuditLog) -> AuditLog:
    db.add(entry)
    db.flush()
    return entry


def list_recent(db: Session, limit: int) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.at.desc()).limit(limit)))
