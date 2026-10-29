import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.modules.audit import service
from app.modules.audit.service import AuditDetailError
from tests.conftest import MakeLogin


async def test_record_appends_with_all_fields(
    app_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    actor, cover = await make_login("manager"), await make_login("manager")
    async with AsyncSession(app_engine) as db:
        await service.record(
            db,
            actor_id=actor.employee_id,
            acting_for_id=cover.employee_id,
            action="request.approve",
            target_type="leave_request",
            target_id="abc",
            detail={"before": {"status": "pending"}, "after": {"status": "approved"}},
            ip="203.0.113.7",
        )
        await db.commit()
        row = (await db.execute(text("SELECT * FROM audit_log"))).mappings().one()
    assert row["actor_id"] == actor.employee_id
    assert row["acting_for_id"] == cover.employee_id
    assert row["detail"]["after"] == {"status": "approved"}
    assert row["ip"] == "203.0.113.7"
    assert row["at"] is not None


@pytest.mark.parametrize("key", ["note", "reason", "token", "password", "sick_type", "Password"])
async def test_forbidden_detail_key_raises(app_engine: AsyncEngine, key: str) -> None:
    async with AsyncSession(app_engine) as db:
        with pytest.raises(AuditDetailError):
            await service.record(
                db, actor_id=None, action="x", target_type="t", detail={key: "anything"}
            )


async def test_forbidden_key_nested_in_before_after_raises(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        with pytest.raises(AuditDetailError):
            await service.record(
                db,
                actor_id=None,
                action="x",
                target_type="t",
                detail={"before": {"status": "pending"}, "after": {"decision_reason": "no"}},
            )


async def test_unknown_detail_key_raises(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        with pytest.raises(AuditDetailError):
            await service.record(
                db, actor_id=None, action="x", target_type="t", detail={"free_text": "hi"}
            )


# R30 append-only, as the restricted app role.
@pytest.mark.parametrize(
    "statement",
    ["UPDATE audit_log SET action = 'tampered'", "DELETE FROM audit_log", "TRUNCATE audit_log"],
)
async def test_audit_log_is_append_only_for_app_role(
    app_engine: AsyncEngine, statement: str
) -> None:
    async with AsyncSession(app_engine) as db:
        await service.record(db, actor_id=None, action="login.failure", target_type="employee")
        await db.commit()
    async with app_engine.connect() as conn:
        with pytest.raises(ProgrammingError, match="permission denied"):
            await conn.execute(text(statement))
    async with app_engine.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM audit_log")) == 1
