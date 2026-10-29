import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.modules.email import privacy
from app.modules.email.templates import Event
from app.modules.identity.models import Employee
from app.modules.notifications.service import emit
from tests.conftest import MakeLogin


async def _employee(db: AsyncSession, employee_id: uuid.UUID) -> Employee:
    emp = await db.get(Employee, employee_id)
    assert emp
    return emp


def _ref(owner: uuid.UUID) -> privacy.RequestRef:
    return privacy.RequestRef(uuid.uuid4(), owner, "Anna", date(2026, 11, 2), date(2026, 11, 2))


async def _count(engine: AsyncEngine, table: str) -> int:
    async with engine.connect() as conn:
        return int((await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one())


# Mock + R35: one mocked outbox row and one notification per event
async def test_emit_writes_mocked_email_and_notification(
    app_engine: AsyncEngine, owner_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    login = await make_login()
    async with async_sessionmaker(app_engine, expire_on_commit=False)() as db:
        emp = await _employee(db, login.employee_id)
        assert await emit(db, Event.REQUEST_APPROVED, emp, ref=_ref(emp.id))
        await db.commit()
    async with owner_engine.connect() as conn:
        row = (await conn.execute(text("SELECT status, to_address, body FROM email_outbox"))).one()
    assert row.status == "mocked"
    assert "http://testserver/requests/" in row.body
    assert await _count(owner_engine, "notification") == 1


async def test_emit_is_idempotent_per_dedupe_key(
    app_engine: AsyncEngine, owner_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    login = await make_login()
    async with async_sessionmaker(app_engine, expire_on_commit=False)() as db:
        emp = await _employee(db, login.employee_id)
        ref = _ref(emp.id)
        assert await emit(db, Event.REQUEST_CREATED, emp, ref=ref)
        assert not await emit(db, Event.REQUEST_CREATED, emp, ref=ref)
        await db.commit()
    assert await _count(owner_engine, "email_outbox") == 1
    assert await _count(owner_engine, "notification") == 1


# Atomicity
async def test_rollback_leaves_no_outbox_or_notification(
    app_engine: AsyncEngine, owner_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    login = await make_login()
    async with async_sessionmaker(app_engine, expire_on_commit=False)() as db:
        emp = await _employee(db, login.employee_id)
        await emit(db, Event.REQUEST_CREATED, emp, ref=_ref(emp.id))
        await db.rollback()
    assert await _count(owner_engine, "email_outbox") == 0
    assert await _count(owner_engine, "notification") == 0


# Invite is email only (R35)
async def test_invite_creates_email_but_no_notification(
    app_engine: AsyncEngine, owner_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    login = await make_login()
    async with async_sessionmaker(app_engine, expire_on_commit=False)() as db:
        emp = await _employee(db, login.employee_id)
        await emit(db, Event.INVITE, emp, link="http://testserver/accept?t=abc", occurrence="t1")
        await db.commit()
    assert await _count(owner_engine, "email_outbox") == 1
    assert await _count(owner_engine, "notification") == 0


async def test_rejection_reason_only_to_the_employee(
    app_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    owner, manager = await make_login(), await make_login("manager")
    async with async_sessionmaker(app_engine, expire_on_commit=False)() as db:
        emp, mgr = await _employee(db, owner.employee_id), await _employee(db, manager.employee_id)
        ref = _ref(emp.id)
        with pytest.raises(privacy.PrivacyError):
            await emit(db, Event.REQUEST_REJECTED, mgr, ref=ref, rejection_reason="no")
        with pytest.raises(privacy.PrivacyError):
            await emit(db, Event.REQUEST_CREATED, emp, ref=ref, rejection_reason="no")
        assert await emit(db, Event.REQUEST_REJECTED, emp, ref=ref, rejection_reason="no")
