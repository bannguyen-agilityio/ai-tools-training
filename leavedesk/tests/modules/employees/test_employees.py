import uuid
from datetime import date
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login, MakeLogin

URL = "/api/v1/hr/employees"


async def rows(owner: AsyncEngine, sql: str, **params: object) -> list[dict]:  # type: ignore[type-arg]
    async with owner.connect() as conn:
        return [dict(r) for r in (await conn.execute(text(sql), params)).mappings()]


def body(**over: object) -> dict[str, object]:
    return {
        "name": "New Person",
        "email": f"n{uuid.uuid4().hex[:6]}@asnet.com.vn",
        "start_date": "2026-01-05",
        **over,
    }


async def create(client: httpx.AsyncClient, hr: Login, **over: object) -> dict[str, Any]:
    r = await client.post(URL, json=body(**over), headers=hr.mutating_headers)
    assert r.status_code == 201, r.text
    created: dict[str, Any] = r.json()
    return created


# --- 401 / 403 matrix ----------------------------------------------------------------------


async def test_unauthenticated_is_401(client: httpx.AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401


@pytest.mark.parametrize("role", ["employee", "manager"])
async def test_non_hr_is_403_everywhere(
    client: httpx.AsyncClient, make_login: MakeLogin, role: str
) -> None:
    user = await make_login(role)
    eid = uuid.uuid4()
    h = user.mutating_headers
    calls = [
        client.get(URL, headers=h),
        client.get(f"{URL}/{eid}", headers=h),
        client.post(URL, json=body(), headers=h),
        client.patch(f"{URL}/{eid}", json={"name": "x"}, headers=h),
        client.post(f"{URL}/{eid}/invite", headers=h),
        client.get("/api/v1/hr/teams", headers=h),
        client.post("/api/v1/hr/teams", json={"name": "T"}, headers=h),
        client.patch(f"/api/v1/hr/teams/{eid}", json={"name": "T"}, headers=h),
    ]
    for call in calls:
        assert (await call).status_code == 403


async def test_deputy_is_403(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    deputy = await make_login("employee")
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :i"), {"i": deputy.employee_id}
        )
    assert (await client.get(URL, headers=deputy.headers)).status_code == 403
    r = await client.post(URL, json=body(), headers=deputy.mutating_headers)
    assert r.status_code == 403


# --- R23 create / edit / audit -------------------------------------------------------------


async def test_create_writes_row_audit_invite_and_no_link(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    r = await client.post(URL, json=body(), headers=hr.mutating_headers)
    assert r.status_code == 201
    assert r.headers["Location"] == f"{URL}/{r.json()['id']}"
    assert "token" not in r.text and "set-password" not in r.text
    emp_id = r.json()["id"]
    audit = await rows(
        owner_engine,
        "SELECT * FROM audit_log WHERE action = 'employee.create' AND target_id = :i",
        i=emp_id,
    )
    assert len(audit) == 1 and audit[0]["actor_id"] == hr.employee_id
    outbox = await rows(owner_engine, "SELECT * FROM email_outbox")
    assert len(outbox) == 1  # R3: exactly one invite


async def test_non_company_domain_is_422(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    r = await client.post(URL, json=body(email="a@gmail.com"), headers=hr.mutating_headers)
    assert r.status_code == 422


async def test_duplicate_email_is_409(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    first = await create(client, hr)
    r = await client.post(URL, json=body(email=first["email"].upper()), headers=hr.mutating_headers)
    assert r.status_code == 409


async def test_unknown_field_refused(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    r = await client.post(URL, json=body(is_active=False), headers=hr.mutating_headers)
    assert r.status_code == 400  # unknown fields are a malformed request (spec 6.1)


async def test_future_year_start_refused(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    r = await client.post(URL, json=body(start_date="2999-01-01"), headers=hr.mutating_headers)
    assert r.status_code == 422


async def test_edit_audits_before_and_after(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    mgr = await create(client, hr, role="manager")
    emp = await create(client, hr)
    r = await client.patch(
        f"{URL}/{emp['id']}", json={"manager_id": mgr["id"]}, headers=hr.mutating_headers
    )
    assert r.status_code == 200 and r.json()["manager_id"] == mgr["id"]
    audit = await rows(
        owner_engine, "SELECT detail FROM audit_log WHERE action = 'employee.update'"
    )
    assert audit[0]["detail"]["before"]["manager_id"] is None
    assert audit[0]["detail"]["after"]["manager_id"] == mgr["id"]


async def test_role_change_is_its_own_audit_action(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    emp = await create(client, hr)
    r = await client.patch(
        f"{URL}/{emp['id']}", json={"role": "manager"}, headers=hr.mutating_headers
    )
    assert r.status_code == 200
    assert (
        len(await rows(owner_engine, "SELECT 1 FROM audit_log WHERE action='employee.role_change'"))
        == 1
    )


@pytest.mark.parametrize(
    ("payload", "status"),
    [
        ({"email": "x@asnet.com.vn"}, 400),  # unknown fields: malformed request (spec 6.1)
        ({"start_date": "2026-02-02"}, 400),
        ({}, 422),
    ],
)
async def test_patch_refuses_immutable_or_empty(
    client: httpx.AsyncClient,
    make_login: MakeLogin,
    payload: dict[str, Any],
    status: int,
) -> None:
    hr = await make_login("hr")
    emp = await create(client, hr)
    r = await client.patch(f"{URL}/{emp['id']}", json=payload, headers=hr.mutating_headers)
    assert r.status_code == status


async def test_missing_employee_is_404(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    assert (await client.get(f"{URL}/{uuid.uuid4()}", headers=hr.headers)).status_code == 404


async def test_list_pagination(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    await create(client, hr)
    await create(client, hr)
    first = (await client.get(f"{URL}?limit=2", headers=hr.headers)).json()
    assert len(first["items"]) == 2 and first["next_cursor"]
    second = (
        await client.get(f"{URL}?limit=2&cursor={first['next_cursor']}", headers=hr.headers)
    ).json()
    assert len(second["items"]) == 1 and second["next_cursor"] is None
    assert (await client.get(f"{URL}?cursor=zzz", headers=hr.headers)).status_code == 422


# --- R23 manager loops ---------------------------------------------------------------------


async def test_direct_loop_refused(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    a, b = await create(client, hr), await create(client, hr)
    h = hr.mutating_headers
    assert (
        await client.patch(f"{URL}/{a['id']}", json={"manager_id": b["id"]}, headers=h)
    ).status_code == 200
    assert (
        await client.patch(f"{URL}/{b['id']}", json={"manager_id": a["id"]}, headers=h)
    ).status_code == 422


async def test_indirect_loop_and_self_refused(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr = await make_login("hr")
    a = await create(client, hr)
    b = await create(client, hr)
    c = await create(client, hr)
    h = hr.mutating_headers
    for child, parent in ((a, b), (b, c)):
        r = await client.patch(f"{URL}/{child['id']}", json={"manager_id": parent["id"]}, headers=h)
        assert r.status_code == 200
    assert (
        await client.patch(f"{URL}/{c['id']}", json={"manager_id": a["id"]}, headers=h)
    ).status_code == 422
    assert (
        await client.patch(f"{URL}/{a['id']}", json={"manager_id": a["id"]}, headers=h)
    ).status_code == 422


# --- R9 ledger -----------------------------------------------------------------------------


async def test_current_year_joiner_gets_prorata(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    year = date.today().year
    emp = await create(client, hr, start_date=f"{year}-07-01")
    got = await rows(
        owner_engine,
        "SELECT leave_type_code, kind, days FROM balance_entry WHERE employee_id = :i",
        i=emp["id"],
    )
    by_type = {r["leave_type_code"]: (r["kind"], float(r["days"])) for r in got}
    assert by_type == {"annual": ("prorata", 6.0), "sick": ("prorata", 3.5)}


async def test_earlier_joiner_gets_normal_entitlement(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    emp = await create(client, hr, start_date="2020-03-02")
    got = await rows(
        owner_engine, "SELECT kind, days FROM balance_entry WHERE employee_id = :i", i=emp["id"]
    )
    assert {r["kind"] for r in got} == {"entitlement"}
    assert sorted(float(r["days"]) for r in got) == [7.0, 12.0]


# --- #20 re-send invite --------------------------------------------------------------------


async def test_resend_invite(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    emp = await create(client, hr)
    r = await client.post(f"{URL}/{emp['id']}/invite", headers=hr.mutating_headers)
    assert r.status_code == 204 and r.content == b""
    assert len(await rows(owner_engine, "SELECT 1 FROM email_outbox")) == 2
