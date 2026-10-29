import httpx

from tests.conftest import MakeLogin


async def test_unauthenticated_is_401(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/audit-log")).status_code == 401


async def test_authorization_is_enforced_per_role(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    emp, mgr, hr = await make_login("employee"), await make_login("manager"), await make_login("hr")
    assert (await client.get("/api/v1/audit-log", headers=emp.headers)).status_code == 403
    assert (await client.get("/api/v1/audit-log", headers=mgr.headers)).status_code == 403
    assert (await client.get("/api/v1/audit-log", headers=hr.headers)).status_code == 200
