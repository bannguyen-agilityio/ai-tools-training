import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.modules.auth.conftest import PASSWORD, MakeUser, User

URL = "/api/v1/auth/password/change"
NEW_PW = "a brand new passphrase"


async def _login(client: httpx.AsyncClient, u: User) -> dict[str, str]:
    r = await client.post("/api/v1/auth/login", json={"email": u.email, "password": PASSWORD})
    return {"X-CSRF-Token": r.json()["csrf_token"]}


async def test_requires_session_and_csrf(client: httpx.AsyncClient, make_user: MakeUser):
    body = {"current_password": PASSWORD, "new_password": NEW_PW}
    assert (await client.post(URL, json=body)).status_code == 401
    u = await make_user()
    await _login(client, u)
    assert (await client.post(URL, json=body)).status_code == 403


async def test_change_keeps_current_kills_others(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user()
    async with httpx.AsyncClient(
        transport=client._transport, base_url="http://testserver"
    ) as other:
        await _login(other, u)
        h = await _login(client, u)
        body = {"current_password": PASSWORD, "new_password": NEW_PW}
        assert (await client.post(URL, json=body, headers=h)).status_code == 204
        assert (await other.get("/api/v1/me")).status_code == 401
    assert (await client.get("/api/v1/me")).status_code == 200
    async with owner_engine.connect() as c:
        n = await c.scalar(text("SELECT count(*) FROM session WHERE employee_id=:e"), {"e": u.id})
    assert n == 1


async def test_wrong_current_and_weak_new(client: httpx.AsyncClient, make_user: MakeUser):
    u = await make_user()
    h = await _login(client, u)
    bad = {"current_password": "wrong-wrong-12", "new_password": NEW_PW}
    assert (await client.post(URL, json=bad, headers=h)).status_code == 403
    weak = {"current_password": PASSWORD, "new_password": "password1234"}
    assert (await client.post(URL, json=weak, headers=h)).status_code == 422
