import uuid
from datetime import date

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.db import make_engine
from app.jobs import drain_outbox
from app.modules.email import privacy
from app.modules.email.outbox_service import drain_due
from app.modules.email.sender import SendError
from app.modules.email.sendgrid_sender import SendGridSender
from app.modules.email.templates import Event
from app.modules.identity.models import Employee
from app.modules.notifications.service import emit
from tests.conftest import MakeLogin
from tests.modules.email.test_outbox_service import _row, _seed


def _patch_transport(monkeypatch: pytest.MonkeyPatch, handler: httpx.MockTransport) -> None:
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: real(transport=handler, **kw),
    )


async def test_sendgrid_success(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(202)

    _patch_transport(monkeypatch, httpx.MockTransport(handler))
    await SendGridSender("key", "from@asnet.com.vn").send(
        to="a@asnet.com.vn", subject="s", body="b"
    )
    assert seen[0].headers["Authorization"] == "Bearer key"


async def test_sendgrid_error_keeps_status_code_only(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_transport(
        monkeypatch, httpx.MockTransport(lambda r: httpx.Response(401, text="leaky body"))
    )
    with pytest.raises(SendError) as exc:
        await SendGridSender("k", "f@x").send(to="a@b.c", subject="s", body="b")
    assert exc.value.code == 401 and "leaky" not in str(exc.value)


async def test_sendgrid_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    _patch_transport(monkeypatch, httpx.MockTransport(boom))
    with pytest.raises(SendError) as exc:
        await SendGridSender("k", "f@x").send(to="a@b.c", subject="s", body="b")
    assert exc.value.code is None


class ExplodingSender:
    async def send(self, *, to: str, subject: str, body: str) -> None:
        raise ValueError("not a SendError")


async def test_unexpected_exception_counts_as_attempt_and_does_not_block(
    app_engine: AsyncEngine, owner_engine: AsyncEngine
) -> None:
    oid = await _seed(owner_engine)
    async with async_sessionmaker(app_engine)() as db:
        await drain_due(db, ExplodingSender())
    row = await _row(owner_engine, oid)
    assert row.attempts == 1 and row.status == "pending" and row.last_error == "ValueError"


async def test_run_once_drains_pending_row(
    owner_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    oid = await _seed(owner_engine)

    class Ok:
        async def send(self, *, to: str, subject: str, body: str) -> None:
            return None

    monkeypatch.setattr(drain_outbox, "get_sender", lambda: Ok())
    monkeypatch.setattr(
        drain_outbox,
        "get_session_factory",
        lambda: async_sessionmaker(make_engine(set_role=True, poolclass=NullPool)),
    )
    assert await drain_outbox.run_once() == 1
    assert (await _row(owner_engine, oid)).status == "sent"


async def test_sick_in_reason_or_name_does_not_block_and_repeat_reset_is_sent(
    app_engine: AsyncEngine, owner_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    login = await make_login()
    async with async_sessionmaker(app_engine, expire_on_commit=False)() as db:
        emp = await db.get(Employee, login.employee_id)
        assert emp
        ref = privacy.RequestRef(
            uuid.uuid4(), emp.id, "Sick Boy", date(2026, 11, 2), date(2026, 11, 2)
        )
        assert await emit(
            db, Event.REQUEST_REJECTED, emp, ref=ref, rejection_reason="you were sick, re-file"
        )
        assert await emit(db, Event.PASSWORD_RESET, emp, link="http://x/1", occurrence="t1")
        assert await emit(db, Event.PASSWORD_RESET, emp, link="http://x/2", occurrence="t2")
        with pytest.raises(ValueError):
            await emit(db, Event.PASSWORD_RESET, emp, link="http://x/3")
        await db.commit()
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(
                text("SELECT count(*) FROM email_outbox WHERE template='password_reset'")
            )
        ).scalar_one()
    assert n == 2
