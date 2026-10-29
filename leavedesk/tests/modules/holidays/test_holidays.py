from datetime import date

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import MakeLogin

APPENDIX_A_2026 = [
    "2026-01-01",
    "2026-02-16",
    "2026-02-17",
    "2026-02-18",
    "2026-02-19",
    "2026-02-20",
    "2026-04-27",
    "2026-04-30",
    "2026-05-01",
    "2026-09-01",
    "2026-09-02",
]
APPENDIX_A_2027 = [
    "2027-01-01",
    "2027-02-08",
    "2027-02-09",
    "2027-02-10",
    "2027-02-11",
    "2027-02-12",
    "2027-04-16",
    "2027-04-30",
    "2027-05-03",
    "2027-09-02",
]


async def audit_rows(owner: AsyncEngine, action: str) -> list[dict]:  # type: ignore[type-arg]
    async with owner.connect() as conn:
        rows = await conn.execute(
            text("SELECT * FROM audit_log WHERE action = :a ORDER BY at"), {"a": action}
        )
        return [dict(r) for r in rows.mappings()]


async def holiday_id(client: httpx.AsyncClient, hr, day: str) -> str:  # type: ignore[no-untyped-def]
    rows = (await client.get(f"/api/v1/holidays?year={day[:4]}", headers=hr.headers)).json()
    return str(next(r["id"] for r in rows if r["holiday_date"] == day))


# --- R11 seed -----------------------------------------------------------------------------


@pytest.mark.parametrize(("year", "expected"), [(2026, APPENDIX_A_2026), (2027, APPENDIX_A_2027)])
async def test_seed_has_every_appendix_a_date(
    client: httpx.AsyncClient, make_login: MakeLogin, year: int, expected: list[str]
) -> None:
    emp = await make_login()
    r = await client.get(f"/api/v1/holidays?year={year}", headers=emp.headers)
    assert r.status_code == 200
    assert [h["holiday_date"] for h in r.json()] == expected
    assert {h["source"] for h in r.json()} == {"seed"}


async def test_year_defaults_to_the_current_company_year(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    emp = await make_login()
    assert (await client.get("/api/v1/holidays", headers=emp.headers)).status_code == 200
    assert (await client.get("/api/v1/holidays?year=1800", headers=emp.headers)).status_code == 422


# --- authorization -------------------------------------------------------------------------


async def test_unauthenticated_is_401(client: httpx.AsyncClient) -> None:
    for method, url in [
        ("GET", "/api/v1/holidays"),
        ("GET", "/api/v1/hr/holidays/impact?date=2026-11-10"),
        ("POST", "/api/v1/hr/holidays"),
        ("PATCH", "/api/v1/hr/holidays/00000000-0000-0000-0000-000000000000"),
        ("DELETE", "/api/v1/hr/holidays/00000000-0000-0000-0000-000000000000"),
    ]:
        assert (await client.request(method, url)).status_code == 401, (method, url)


@pytest.mark.parametrize("role", ["employee", "manager"])
async def test_non_hr_cannot_manage_holidays(
    client: httpx.AsyncClient, make_login: MakeLogin, role: str
) -> None:
    hr, user = await make_login("hr"), await make_login(role)
    hid = await holiday_id(client, hr, "2026-09-02")
    assert (await client.get("/api/v1/holidays", headers=user.headers)).status_code == 200
    h = user.mutating_headers
    assert (
        await client.get("/api/v1/hr/holidays/impact?date=2026-09-02", headers=user.headers)
    ).status_code == 403
    body = {"holiday_date": "2026-11-20", "name": "X"}
    assert (await client.post("/api/v1/hr/holidays", json=body, headers=h)).status_code == 403
    assert (
        await client.patch(f"/api/v1/hr/holidays/{hid}", json={"name": "X"}, headers=h)
    ).status_code == 403
    assert (await client.delete(f"/api/v1/hr/holidays/{hid}", headers=h)).status_code == 403


async def test_deputy_has_no_holiday_admin_rights(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    deputy = await make_login("employee")
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :i"), {"i": deputy.employee_id}
        )
    r = await client.post(
        "/api/v1/hr/holidays",
        json={"holiday_date": "2026-11-20", "name": "X"},
        headers=deputy.mutating_headers,
    )
    assert r.status_code == 403


async def test_mutations_need_csrf(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    r = await client.post(
        "/api/v1/hr/holidays", json={"holiday_date": "2026-11-20", "name": "X"}, headers=hr.headers
    )
    assert r.status_code == 403


# --- CRUD, audit, impact -------------------------------------------------------------------


async def test_add_holiday_is_audited_and_listed(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    r = await client.post(
        "/api/v1/hr/holidays",
        json={"holiday_date": "2026-11-20", "name": "Teachers' Day"},
        headers=hr.mutating_headers,
    )
    assert r.status_code == 201
    assert r.json()["affected_requests"] == 0
    assert r.json()["holiday"]["source"] == "manual"
    listed = (await client.get("/api/v1/holidays?year=2026", headers=hr.headers)).json()
    assert "2026-11-20" in [h["holiday_date"] for h in listed]
    (row,) = await audit_rows(owner_engine, "holiday.create")
    assert row["actor_id"] == hr.employee_id and row["target_type"] == "public_holiday"
    assert row["detail"]["after"] == {"holiday_date": "2026-11-20", "name": "Teachers' Day"}


async def test_duplicate_date_is_409(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    r = await client.post(
        "/api/v1/hr/holidays",
        json={"holiday_date": "2026-09-02", "name": "Again"},
        headers=hr.mutating_headers,
    )
    assert r.status_code == 409


async def test_strict_body_and_validation(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    h = hr.mutating_headers
    url = "/api/v1/hr/holidays"
    assert (
        await client.post(url, json={"holiday_date": "2026-11-20", "name": "X", "x": 1}, headers=h)
    ).status_code == 422
    assert (
        await client.post(url, json={"holiday_date": "2026-11-20", "name": " "}, headers=h)
    ).status_code == 422
    assert (
        await client.post(url, json={"holiday_date": "1800-01-01", "name": "X"}, headers=h)
    ).status_code == 422
    hid = await holiday_id(client, hr, "2026-09-02")
    assert (await client.patch(f"{url}/{hid}", json={}, headers=h)).status_code == 422


async def test_edit_records_before_and_after(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    hid = await holiday_id(client, hr, "2026-09-01")
    r = await client.patch(
        f"/api/v1/hr/holidays/{hid}",
        json={"holiday_date": "2026-09-03", "name": "National Day (extra)"},
        headers=hr.mutating_headers,
    )
    assert r.status_code == 200 and r.json()["holiday"]["holiday_date"] == "2026-09-03"
    (row,) = await audit_rows(owner_engine, "holiday.update")
    assert row["detail"]["before"] == {"holiday_date": "2026-09-01", "name": "National Day"}
    assert row["detail"]["after"]["holiday_date"] == "2026-09-03"
    clash = await client.patch(
        f"/api/v1/hr/holidays/{hid}",
        json={"holiday_date": "2026-09-02"},
        headers=hr.mutating_headers,
    )
    assert clash.status_code == 409


async def test_delete_is_audited_and_missing_is_404(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    hid = await holiday_id(client, hr, "2026-05-01")
    r = await client.delete(f"/api/v1/hr/holidays/{hid}", headers=hr.mutating_headers)
    assert r.status_code == 200 and r.json()["holiday"]["holiday_date"] == "2026-05-01"
    assert (await audit_rows(owner_engine, "holiday.delete"))[0]["detail"]["before"][
        "holiday_date"
    ] == "2026-05-01"
    again = await client.delete(f"/api/v1/hr/holidays/{hid}", headers=hr.mutating_headers)
    assert again.status_code == 404


async def test_holiday_inside_an_approved_request_is_counted_and_nothing_is_rewritten(
    client: httpx.AsyncClient,
    make_login: MakeLogin,
    make_request,  # type: ignore[no-untyped-def]
    owner_engine: AsyncEngine,
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    rid = await make_request(emp.employee_id, date(2026, 11, 16), date(2026, 11, 20))
    await make_request(emp.employee_id, date(2026, 11, 23), date(2026, 11, 23), status="rejected")
    await make_request(emp.employee_id, date(2026, 11, 24), date(2026, 11, 24), status="cancelled")
    async with owner_engine.connect() as conn:
        before = (
            (await conn.execute(text("SELECT * FROM leave_request ORDER BY id"))).mappings().all()
        )
        days_before = (
            await conn.execute(text("SELECT count(*) FROM leave_request_day"))
        ).scalar_one()

    impact = await client.get("/api/v1/hr/holidays/impact?date=2026-11-18", headers=hr.headers)
    assert impact.json() == {"holiday_date": "2026-11-18", "affected_requests": 1}
    # Only Pending/Approved count, and only on a weekday.
    for day in ("2026-11-23", "2026-11-24", "2026-11-21"):
        r = await client.get(f"/api/v1/hr/holidays/impact?date={day}", headers=hr.headers)
        assert r.json()["affected_requests"] == 0, day

    r = await client.post(
        "/api/v1/hr/holidays",
        json={"holiday_date": "2026-11-18", "name": "Extra day off"},
        headers=hr.mutating_headers,
    )
    assert r.status_code == 201 and r.json()["affected_requests"] == 1
    (row,) = await audit_rows(owner_engine, "holiday.create")
    assert row["detail"]["count"] == 1

    # C-8: the request header and its day rows are untouched.
    async with owner_engine.connect() as conn:
        after = (
            (await conn.execute(text("SELECT * FROM leave_request ORDER BY id"))).mappings().all()
        )
        days_after = (
            await conn.execute(text("SELECT count(*) FROM leave_request_day"))
        ).scalar_one()
        working = (
            await conn.execute(
                text("SELECT working_days FROM leave_request WHERE id = :i"), {"i": rid}
            )
        ).scalar_one()
    assert [dict(x) for x in after] == [dict(x) for x in before]
    assert days_after == days_before and working == 5

    # Deleting it again also reports the request, and still changes nothing.
    hid = r.json()["holiday"]["id"]
    d = await client.delete(f"/api/v1/hr/holidays/{hid}", headers=hr.mutating_headers)
    assert d.json()["affected_requests"] == 1
    async with owner_engine.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT working_days FROM leave_request WHERE id = :i"), {"i": rid}
            )
        ).scalar_one() == 5


async def test_moving_a_holiday_counts_requests_on_the_old_and_the_new_date(
    client: httpx.AsyncClient,
    make_login: MakeLogin,
    make_request,  # type: ignore[no-untyped-def]
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    await make_request(emp.employee_id, date(2026, 9, 1), date(2026, 9, 1))  # on the old date
    await make_request(emp.employee_id, date(2026, 9, 3), date(2026, 9, 3))  # on the new date
    hid = await holiday_id(client, hr, "2026-09-01")
    r = await client.patch(
        f"/api/v1/hr/holidays/{hid}",
        json={"holiday_date": "2026-09-03"},
        headers=hr.mutating_headers,
    )
    assert r.json()["affected_requests"] == 2


async def test_noop_edit_writes_no_audit_row_and_keeps_source(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    hid = await holiday_id(client, hr, "2026-09-02")
    r = await client.patch(
        f"/api/v1/hr/holidays/{hid}", json={"name": "National Day"}, headers=hr.mutating_headers
    )
    assert r.status_code == 200 and r.json()["holiday"]["source"] == "seed"
    assert await audit_rows(owner_engine, "holiday.update") == []
