from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.modules.auth import service
from app.modules.auth.purge import purge
from app.modules.email.outbox_service import drain_due
from app.modules.identity.models import Employee
from tests.modules.auth.conftest import MakeUser


async def test_purge_removes_only_stale_rows(
    make_user: MakeUser, app_engine: AsyncEngine, owner_engine: AsyncEngine
):
    u = await make_user()
    now = datetime.now(UTC)
    async with owner_engine.connect() as c:
        await c.execute(
            text(
                "INSERT INTO login_attempt (email_hash, ip, at, success) VALUES "
                "('a','1',:old,false),('b','1',:new,false)"
            ),
            {"old": now - timedelta(days=31), "new": now - timedelta(days=1)},
        )
        await c.execute(
            text(
                "INSERT INTO one_time_token (employee_id,purpose,token_hash,expires_at,used_at) "
                "VALUES (:e,'reset','h1',:past,NULL),(:e,'reset','h2',:future,NULL),"
                "(:e,'reset','h3',:future,:past)"
            ),
            {"e": u.id, "past": now - timedelta(hours=1), "future": now + timedelta(hours=1)},
        )
    async with AsyncSession(app_engine) as s:
        result = await purge(s, now)
        assert result["attempts"] == 1 and result["tokens"] == 2
        assert (await purge(s, now)) == {"sessions": 0, "tokens": 0, "attempts": 0}  # idempotent
    async with owner_engine.connect() as c:
        left = (await c.execute(text("SELECT token_hash FROM one_time_token"))).scalars().all()
    assert left == ["h2"]


class _Ok:
    async def send(self, *, to: str, subject: str, body: str) -> None:
        return None


async def test_link_removed_from_outbox_after_delivery(
    make_user: MakeUser, app_engine: AsyncEngine, owner_engine: AsyncEngine
):
    u = await make_user(password=None)
    async with AsyncSession(app_engine, expire_on_commit=False) as s:
        e = await s.get(Employee, u.id)
        assert e
        token = await service.issue_invite(s, e)
        await s.commit()
    async with owner_engine.connect() as c:
        await c.execute(text("UPDATE email_outbox SET status='pending'"))
    async with AsyncSession(app_engine) as s:
        assert await drain_due(s, _Ok()) == 1
    async with owner_engine.connect() as c:
        row = (await c.execute(text("SELECT body, payload::text FROM email_outbox"))).one()
    assert token not in row[0] and token not in row[1]
