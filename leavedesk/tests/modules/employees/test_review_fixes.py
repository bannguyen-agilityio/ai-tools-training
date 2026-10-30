import base64

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import MakeLogin

URL = "/api/v1/hr/employees"


async def test_hr_cannot_change_own_role(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    r = await client.patch(
        f"{URL}/{hr.employee_id}", json={"role": "employee"}, headers=hr.mutating_headers
    )
    assert r.status_code == 422


async def test_huge_cursor_is_422(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    cursor = base64.urlsafe_b64encode(b"99999999999999999999").decode()
    r = await client.get(f"{URL}?cursor={cursor}", headers=hr.headers)
    assert r.status_code == 422


async def test_edit_with_unchanged_inactive_manager_succeeds(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    mgr = await make_login("manager")
    h = hr.mutating_headers
    body = {"name": "Eli", "email": "eli@asnet.com.vn", "start_date": "2020-01-06"}
    emp = (
        await client.post(URL, json={**body, "manager_id": str(mgr.employee_id)}, headers=h)
    ).json()
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_active = false WHERE id = :i"), {"i": mgr.employee_id}
        )
    r = await client.patch(
        f"{URL}/{emp['id']}", json={"name": "Eli B", "manager_id": str(mgr.employee_id)}, headers=h
    )
    assert r.status_code == 200 and r.json()["name"] == "Eli B"


async def test_mixed_case_email_is_normalised(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr = await make_login("hr")
    body = {"name": "Mixed", "email": "Mixed.Case@ASNET.COM.VN", "start_date": "2020-01-06"}
    r = await client.post(URL, json=body, headers=hr.mutating_headers)
    assert r.status_code == 201
    assert r.json()["email"] == "mixed.case@asnet.com.vn"
