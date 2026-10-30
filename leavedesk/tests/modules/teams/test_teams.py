import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import MakeLogin

URL = "/api/v1/hr/teams"


async def test_unauthenticated_is_401(client: httpx.AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401


async def test_team_crud_and_audit(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    h = hr.mutating_headers
    r = await client.post(URL, json={"name": "Platform"}, headers=h)
    assert r.status_code == 201 and r.headers["Location"] == f"{URL}/{r.json()['id']}"
    tid = r.json()["id"]
    r = await client.patch(
        f"{URL}/{tid}", json={"name": "Platform 2", "manager_id": str(hr.employee_id)}, headers=h
    )
    assert r.status_code == 200 and r.json()["name"] == "Platform 2"
    assert [t["name"] for t in (await client.get(URL, headers=hr.headers)).json()["items"]] == [
        "Platform 2"
    ]
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(text("SELECT count(*) FROM audit_log WHERE action LIKE 'team.%'"))
        ).scalar()
    assert n == 2


async def test_duplicate_name_409_and_bad_manager_422(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr = await make_login("hr")
    h = hr.mutating_headers
    assert (await client.post(URL, json={"name": "A"}, headers=h)).status_code == 201
    assert (await client.post(URL, json={"name": "A"}, headers=h)).status_code == 409
    bad = {"name": "B", "manager_id": "00000000-0000-0000-0000-000000000000"}
    assert (await client.post(URL, json=bad, headers=h)).status_code == 422
