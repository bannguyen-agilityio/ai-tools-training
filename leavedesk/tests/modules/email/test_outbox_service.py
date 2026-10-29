import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.modules.email.outbox_service import BACKOFF, MAX_ATTEMPTS, drain_due
from app.modules.email.sender import SendError
from tests.conftest import MakeLogin


class StubSender:
    def __init__(self, fail_with: int | None = None) -> None:
        self.fail_with = fail_with
        self.calls = 0

    async def send(self, *, to: str, subject: str, body: str) -> None:
        self.calls += 1
        if self.fail_with is not None:
            raise SendError(self.fail_with)


async def _seed(engine: AsyncEngine, status: str = "pending") -> uuid.UUID:
    oid = uuid.uuid4()
    async with engine.connect() as conn:
        await conn.execute(
            text(
                "INSERT INTO email_outbox (id, to_address, template, subject, body, dedupe_key, "
                "status) VALUES (:i, 'a@asnet.com.vn', 'request_approved', 's', 'b', :k, :s)"
            ),
            {"i": oid, "k": str(oid), "s": status},
        )
    return oid


async def _row(engine: AsyncEngine, oid: uuid.UUID) -> Any:
    async with engine.connect() as conn:
        return (
            await conn.execute(text("SELECT * FROM email_outbox WHERE id = :i"), {"i": oid})
        ).one()


async def test_success_marks_sent(app_engine: AsyncEngine, owner_engine: AsyncEngine) -> None:
    oid = await _seed(owner_engine)
    sender = StubSender()
    async with async_sessionmaker(app_engine)() as db:
        assert await drain_due(db, sender) == 1
    row = await _row(owner_engine, oid)
    assert (row.status, row.attempts, row.sent_at is not None) == ("sent", 0, True)


async def test_failures_follow_backoff_then_fail(
    app_engine: AsyncEngine, owner_engine: AsyncEngine
) -> None:
    oid = await _seed(owner_engine)
    sender = StubSender(fail_with=503)
    now = datetime.now(UTC)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        async with async_sessionmaker(app_engine)() as db:
            await drain_due(db, sender, now)
        row = await _row(owner_engine, oid)
        assert row.attempts == attempt
        assert row.last_error == "503"
        if attempt < MAX_ATTEMPTS:
            assert row.status == "pending"
            assert abs(row.next_try_at - (now + BACKOFF[attempt - 1])) < timedelta(seconds=1)
            now = row.next_try_at  # time passes
    assert row.status == "failed"
    # a failed row is never picked up again
    async with async_sessionmaker(app_engine)() as db:
        assert await drain_due(db, sender, now + timedelta(days=2)) == 0


async def test_not_due_rows_are_skipped(app_engine: AsyncEngine, owner_engine: AsyncEngine) -> None:
    oid = await _seed(owner_engine)
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE email_outbox SET next_try_at = now() + interval '1 hour' WHERE id=:i"),
            {"i": oid},
        )
    sender = StubSender()
    async with async_sessionmaker(app_engine)() as db:
        assert await drain_due(db, sender) == 0
    assert sender.calls == 0


async def test_mocked_rows_are_never_sent(
    app_engine: AsyncEngine, owner_engine: AsyncEngine
) -> None:
    await _seed(owner_engine, "mocked")
    sender = StubSender()
    async with async_sessionmaker(app_engine)() as db:
        await drain_due(db, sender)
    assert sender.calls == 0


# HR endpoints (#31): 401 / 403 per role, list, retry (audited)
async def test_hr_outbox_endpoints_require_hr(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    oid = uuid.uuid4()
    assert (await client.get("/api/v1/hr/email-outbox")).status_code == 401
    assert (await client.post(f"/api/v1/hr/email-outbox/{oid}/retry")).status_code == 401
    for role in ("employee", "manager"):
        login = await make_login(role)
        r = await client.get("/api/v1/hr/email-outbox", headers=login.headers)
        assert r.status_code == 403
        r = await client.post(
            f"/api/v1/hr/email-outbox/{oid}/retry", headers=login.mutating_headers
        )
        assert r.status_code == 403


async def test_hr_sees_failed_and_retries_with_audit(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    failed, sent = await _seed(owner_engine, "failed"), await _seed(owner_engine, "sent")
    r = await client.get("/api/v1/hr/email-outbox?status=failed", headers=hr.headers)
    assert [e["id"] for e in r.json()] == [str(failed)]
    assert "body" not in r.json()[0] and "payload" not in r.json()[0]

    url = "/api/v1/hr/email-outbox/{}/retry"
    assert (await client.post(url.format(sent), headers=hr.mutating_headers)).status_code == 409
    missing = await client.post(url.format(uuid.uuid4()), headers=hr.mutating_headers)
    assert missing.status_code == 404
    ok = await client.post(url.format(failed), headers=hr.mutating_headers)
    assert ok.status_code == 200 and ok.json()["status"] == "pending"
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(text("SELECT count(*) FROM audit_log WHERE action='email.retry'"))
        ).scalar_one()
    assert n == 1
