import httpx

from tests.conftest import MakeLogin

URL = "/api/v1/hr/employees"


async def test_hr_cannot_change_own_role(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    r = await client.patch(
        f"{URL}/{hr.employee_id}", json={"role": "employee"}, headers=hr.mutating_headers
    )
    assert r.status_code == 422


async def test_mixed_case_email_is_normalised(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr = await make_login("hr")
    body = {"name": "Mixed", "email": "Mixed.Case@ASNET.COM.VN", "start_date": "2020-01-06"}
    r = await client.post(URL, json=body, headers=hr.mutating_headers)
    assert r.status_code == 201
    assert r.json()["email"] == "mixed.case@asnet.com.vn"
