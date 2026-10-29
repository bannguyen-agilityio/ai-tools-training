import uuid

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import MakeLogin


async def _notify(engine: AsyncEngine, employee_id: uuid.UUID) -> uuid.UUID:
    nid = uuid.uuid4()
    async with engine.connect() as conn:
        await conn.execute(
            text(
                "INSERT INTO notification (id, employee_id, kind, title, body, link, dedupe_key) "
                "VALUES (:i, :e, 'request_created', 't', 'b', '/requests/1', :k)"
            ),
            {"i": nid, "e": employee_id, "k": str(nid)},
        )
    return nid


async def _unread(client: httpx.AsyncClient, headers: dict[str, str]) -> int:
    body = (await client.get("/api/v1/notifications", headers=headers)).json()
    return int(body["unread_count"])


async def test_unauthenticated_is_401(client: httpx.AsyncClient) -> None:
    nid = uuid.uuid4()
    assert (await client.get("/api/v1/notifications")).status_code == 401
    assert (await client.post(f"/api/v1/notifications/{nid}/read")).status_code == 401
    assert (await client.post("/api/v1/notifications/read-all")).status_code == 401


async def test_list_shows_only_own_with_unread_count(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    me, other = await make_login(), await make_login()
    mine = await _notify(owner_engine, me.employee_id)
    await _notify(owner_engine, other.employee_id)
    body = (await client.get("/api/v1/notifications", headers=me.headers)).json()
    assert body["unread_count"] == 1
    assert [n["id"] for n in body["items"]] == [str(mine)]


async def test_opening_marks_read(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    me = await make_login()
    nid = await _notify(owner_engine, me.employee_id)
    r = await client.post(f"/api/v1/notifications/{nid}/read", headers=me.mutating_headers)
    assert r.status_code == 200 and r.json()["read_at"] and r.json()["link"] == "/requests/1"
    assert await _unread(client, me.headers) == 0


async def test_someone_elses_notification_is_403_and_stays_unread(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    me, other = await make_login(), await make_login("hr")
    nid = await _notify(owner_engine, me.employee_id)
    r = await client.post(f"/api/v1/notifications/{nid}/read", headers=other.mutating_headers)
    assert r.status_code == 403
    assert await _unread(client, me.headers) == 1
    missing = await client.post(
        f"/api/v1/notifications/{uuid.uuid4()}/read", headers=me.mutating_headers
    )
    assert missing.status_code == 404


async def test_read_all_only_touches_own(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    me, other = await make_login(), await make_login()
    await _notify(owner_engine, me.employee_id)
    await _notify(owner_engine, other.employee_id)
    r = await client.post("/api/v1/notifications/read-all", headers=me.mutating_headers)
    assert r.status_code == 204
    assert await _unread(client, me.headers) == 0
    assert await _unread(client, other.headers) == 1
