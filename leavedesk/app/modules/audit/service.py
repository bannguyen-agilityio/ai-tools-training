import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import FORBIDDEN_KEYS
from app.modules.audit import repository
from app.modules.audit.models import AuditLog

# Detail may carry ids and before/after values of non-sensitive fields only (R30).
ALLOWED_DETAIL_KEYS = frozenset(
    {
        "before",
        "after",
        "employee_id",
        "request_id",
        "status",
        "version",
        "days",
        "leave_year",
        "holiday_date",
        "role",
        "fields",
        "count",
        "format",
        "reason_code",
    }
)


class AuditDetailError(ValueError):
    pass


def _check(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise AuditDetailError(f"forbidden audit field: {path}{key}")
            _check(inner, f"{path}{key}.")
    elif isinstance(value, list | tuple):
        for inner in value:
            _check(inner, path)


def validate_detail(detail: dict[str, Any]) -> None:
    for key in detail:
        if str(key).lower() in FORBIDDEN_KEYS:
            raise AuditDetailError(f"forbidden audit field: {key}")
        if key not in ALLOWED_DETAIL_KEYS:
            raise AuditDetailError(f"audit field not in allow-list: {key}")
    _check(detail, "")


async def record(
    db: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    target_type: str,
    target_id: str | None = None,
    detail: dict[str, Any] | None = None,
    acting_for_id: uuid.UUID | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Append one audit row in the caller's transaction (it commits or rolls back with it)."""
    detail = detail or {}
    validate_detail(detail)
    entry = AuditLog(
        actor_id=actor_id,
        acting_for_id=acting_for_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip=ip,
    )
    return await repository.add(db, entry)
