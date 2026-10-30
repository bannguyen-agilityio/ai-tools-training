import asyncio
import uuid
from datetime import date

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login
from tests.modules.balances.test_ledger_jobs import seed_year

CREATE = "/api/v1/requests"
PREVIEW = "/api/v1/requests/preview"


def body(start: str = "2026-06-08", end: str | None = None, **kw: object) -> dict[str, object]:
    return {
        "leave_type": "annual",
        "start_date": start,
        "end_date": end or start,
        "start_part": "full",
        "end_part": "full",
        **kw,
    }


async def post(
    client: httpx.AsyncClient, who: Login, payload: dict[str, object], url: str = CREATE
) -> httpx.Response:
    return await client.post(url, json=payload, headers=who.mutating_headers)


async def outbox(owner: AsyncEngine, template: str = "request_created") -> list[str]:
    async with owner.connect() as conn:
        rows = await conn.execute(
            text("SELECT recipient_employee_id FROM email_outbox WHERE template = :t"),
            {"t": template},
        )
        return [str(r[0]) for r in rows]


# --- AuthZ ---------------------------------------------------------------------------------


async def test_requires_session_and_csrf(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    for method, url in (("POST", CREATE), ("POST", PREVIEW), ("GET", "/api/v1/me/requests")):
        r = await client.request(method, url, json=body() if method == "POST" else None)
        assert r.status_code == 401
    assert (await client.post(CREATE, json=body(), headers=emp.headers)).status_code == 403


async def test_unknown_fields_refused(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    r = await post(client, staff[0], body(status="approved"))
    assert r.status_code == 400


# --- R12 -----------------------------------------------------------------------------------


async def test_create_full_days(
    client: httpx.AsyncClient, staff, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    r = await post(client, emp, body("2026-06-08", "2026-06-10", note="trip"))
    assert r.status_code == 201
    j = r.json()
    assert r.headers["Location"] == f"/api/v1/requests/{j['id']}"
    assert (j["status"], j["working_days"], j["queue"], j["version"]) == (
        "pending",
        3.0,
        "manager",
        1,
    )
    assert j["assigned_to"] == str(mgr.employee_id) and j["note"] == "trip"
    async with owner_engine.connect() as conn:
        n = await conn.scalar(
            text("SELECT count(*) FROM leave_request_day WHERE request_id = :r AND is_active"),
            {"r": uuid.UUID(j["id"])},
        )
    assert n == 6  # two half-day rows per full day


@pytest.mark.parametrize(
    ("start", "end", "sp", "ep", "days"),
    [
        ("2026-06-08", "2026-06-08", "am", "am", 0.5),
        ("2026-06-08", "2026-06-08", "pm", "pm", 0.5),
        ("2026-06-08", "2026-06-10", "pm", "am", 2.0),  # Mon pm, Tue full, Wed am
    ],
)
async def test_half_day_shapes(client, staff, start, end, sp, ep, days) -> None:  # type: ignore[no-untyped-def]
    r = await post(client, staff[0], body(start, end, start_part=sp, end_part=ep))
    assert r.status_code == 201 and r.json()["working_days"] == days


@pytest.mark.parametrize(
    ("end", "sp", "ep", "field"),
    [
        ("2026-06-10", "am", "full", "start_part"),
        ("2026-06-10", "full", "pm", "end_part"),
        ("2026-06-08", "am", "pm", "end_part"),
    ],
)
async def test_bad_part_shapes(client, staff, end, sp, ep, field) -> None:  # type: ignore[no-untyped-def]
    r = await post(client, staff[0], body("2026-06-08", end, start_part=sp, end_part=ep))
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == field


async def test_no_working_days_and_blank_note(client, staff) -> None:  # type: ignore[no-untyped-def]
    r = await post(client, staff[0], body("2026-06-06", "2026-06-07"))  # Sat-Sun
    assert r.status_code == 422 and r.json()["error"]["code"] == "NO_WORKING_DAYS"
    ok = await post(client, staff[0], body(note="   "))
    assert ok.status_code == 201 and ok.json()["note"] is None
    assert (await post(client, staff[0], body("2026-06-15", note="x" * 501))).status_code == 422


async def test_insufficient_balance(client, staff) -> None:  # type: ignore[no-untyped-def]
    r = await post(client, staff[0], body("2026-06-08", "2026-06-26"))  # 15 days vs 12
    assert r.status_code == 422 and r.json()["error"]["code"] == "INSUFFICIENT_BALANCE"


async def test_unpaid_needs_no_balance(client, staff) -> None:  # type: ignore[no-untyped-def]
    r = await post(client, staff[0], body("2026-06-08", "2026-07-17", leave_type="unpaid"))
    assert r.status_code == 201


# --- R13 -----------------------------------------------------------------------------------


async def test_end_before_start(client, staff) -> None:  # type: ignore[no-untyped-def]
    r = await post(client, staff[0], body("2026-06-10", "2026-06-09"))
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "end_date"


async def test_overlap_names_conflict_but_am_pm_ok(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp = staff[0]
    assert (
        await post(client, emp, body("2026-06-08", start_part="am", end_part="am"))
    ).status_code == 201
    pm = await post(client, emp, body("2026-06-08", start_part="pm", end_part="pm"))
    assert pm.status_code == 201
    r = await post(client, emp, body("2026-06-05", "2026-06-09"))
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "OVERLAP" and "Mon 8 Jun 2026" in err["message"]
    assert "annual" not in err["message"].lower()


async def test_cancelled_leave_does_not_block(client, staff, make_request) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    await make_request(emp.employee_id, date(2026, 6, 8), date(2026, 6, 8), status="rejected")
    assert (await post(client, emp, body("2026-06-08"))).status_code == 201


async def test_concurrent_identical_submits_one_wins(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    rs = await asyncio.gather(*(post(client, emp, body("2026-06-09")) for _ in range(2)))
    assert sorted(r.status_code for r in rs) == [201, 409]


async def test_concurrent_submits_cannot_overspend(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    a, b = body("2026-06-08", "2026-06-19"), body("2026-06-22", "2026-07-03")  # 10 + 10 vs 12
    rs = await asyncio.gather(post(client, emp, a), post(client, emp, b))
    assert sorted(r.status_code for r in rs) == [201, 422]


async def test_past_start(client, staff) -> None:  # type: ignore[no-untyped-def]
    for leave_type in ("annual", "unpaid"):
        r = await post(client, staff[0], body("2026-05-29", leave_type=leave_type))
        assert r.status_code == 422 and r.json()["error"]["details"][0]["field"] == "start_date"
    # Today is not "in the past"; a single day today is the notice rule (R14), so use two days.
    assert (await post(client, staff[0], body("2026-06-01", "2026-06-02"))).status_code == 201


# --- R17 -----------------------------------------------------------------------------------


async def test_employee_routes_to_manager_with_email(client, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    assert (await post(client, emp, body())).status_code == 201
    assert await outbox(owner_engine) == [str(mgr.employee_id)]
    async with owner_engine.connect() as conn:
        n = await conn.scalar(
            text("SELECT count(*) FROM notification WHERE employee_id = :m"),
            {"m": mgr.employee_id},
        )
    assert n == 1


async def test_manager_routes_to_hr_approvers(client, make_login, owner_engine) -> None:  # type: ignore[no-untyped-def]
    mgr, hr, deputy, other = (
        await make_login("manager"),
        await make_login("hr"),
        await make_login("employee"),
        await make_login("employee"),
    )
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :d"), {"d": deputy.employee_id}
        )
    await seed_year(owner_engine, mgr.employee_id, "entitlement", "12")
    r = await post(client, mgr, body())
    assert r.status_code == 201
    assert (r.json()["queue"], r.json()["assigned_to"]) == ("hr", None)
    assert sorted(await outbox(owner_engine)) == sorted(
        [str(hr.employee_id), str(deputy.employee_id)]
    )
    assert str(other.employee_id) not in await outbox(owner_engine)


async def test_unroutable_requests_refused(client, make_login) -> None:  # type: ignore[no-untyped-def]
    no_manager = await make_login()
    r = await post(client, no_manager, body("2026-06-08", leave_type="unpaid"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "NO_APPROVER"
    hr = await make_login("hr")
    r = await post(client, hr, body("2026-06-08", leave_type="unpaid"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "ROUTE_UNAVAILABLE"


async def test_manager_with_no_hr_approver_refused(client, make_login) -> None:  # type: ignore[no-untyped-def]
    lone_manager = await make_login("manager")
    r = await post(client, lone_manager, body("2026-06-08", leave_type="unpaid"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "NO_APPROVER"


async def test_inactive_manager_refused(client, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_active = false WHERE id = :m"), {"m": staff[1].employee_id}
        )
    assert (await post(client, staff[0], body())).json()["error"]["code"] == "NO_APPROVER"


async def test_own_decision_check_in_db(owner_engine, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    with pytest.raises(Exception, match="ck_leave_request"):
        async with owner_engine.connect() as conn:
            await conn.execute(
                text(
                    "INSERT INTO leave_request (employee_id, leave_type_code, start_date,"
                    " start_part, end_date, end_part, working_days, queue, decided_by)"
                    " VALUES (:e, 'annual', '2026-06-08', 'full', '2026-06-08', 'full', 1,"
                    " 'manager', :e)"
                ),
                {"e": emp.employee_id},
            )


# --- privacy / audit -----------------------------------------------------------------------


async def test_audit_and_email_hold_no_type_or_note(client, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    await seed_year(owner_engine, emp.employee_id, "entitlement", "7", type="sick")
    r = await post(client, emp, body("2026-06-08", leave_type="sick", note="migraine"))
    assert r.status_code == 201
    async with owner_engine.connect() as conn:
        audit = str(
            (
                await conn.execute(
                    text("SELECT detail FROM audit_log WHERE action = 'request.create'")
                )
            ).all()
        )
        mail = str(
            (await conn.execute(text("SELECT subject, body, payload FROM email_outbox"))).all()
        )
        notes = str((await conn.execute(text("SELECT title, body FROM notification"))).all())
    for blob in (audit, mail, notes):
        assert "sick" not in blob.lower() and "migraine" not in blob


async def test_sick_redaction_by_viewer(client, staff, make_login, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    await seed_year(owner_engine, emp.employee_id, "entitlement", "7", type="sick")
    rid = (await post(client, emp, body("2026-06-08", leave_type="sick", note="private"))).json()[
        "id"
    ]
    url = f"{CREATE}/{rid}"
    own = (await client.get(url, headers=emp.headers)).json()
    assert (own["leave_type"], own["note"]) == ("sick", "private")
    deciding = (await client.get(url, headers=mgr.headers)).json()
    assert (deciding["leave_type"], deciding["note"]) == ("sick", "private")
    hr = await make_login("hr")
    assert (await client.get(url, headers=hr.headers)).json()["leave_type"] == "sick"
    # Once decided the manager only sees "Off".
    async with owner_engine.connect() as conn:
        await conn.execute(text("UPDATE leave_request SET status = 'approved'"))
    after = (await client.get(url, headers=mgr.headers)).json()
    assert after["leave_type"] is None and after["note"] is None and after["label"] == "Off"
    assert "sick" not in str(after).lower() and "private" not in str(after)


async def test_get_authz(client, staff, make_login) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = (await post(client, emp, body())).json()["id"]
    url = f"{CREATE}/{rid}"
    assert (await client.get(url)).status_code == 401
    stranger = await make_login()
    assert (await client.get(url, headers=stranger.headers)).status_code == 403
    assert (await client.get(url, headers=mgr.headers)).status_code == 200
    assert (await client.get(f"{CREATE}/{uuid.uuid4()}", headers=emp.headers)).status_code == 404


async def test_unrelated_manager_cannot_read_pending_sick(
    client, staff, make_login, owner_engine
) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    await seed_year(owner_engine, emp.employee_id, "entitlement", "7", type="sick")
    rid = (await post(client, emp, body("2026-06-08", leave_type="sick", note="private"))).json()[
        "id"
    ]
    other_mgr = await make_login("manager")
    resp = await client.get(f"{CREATE}/{rid}", headers=other_mgr.headers)
    assert resp.status_code == 403
    assert "sick" not in resp.text.lower() and "private" not in resp.text


async def test_my_requests_list_filters_and_paging(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    for d in ("2026-06-08", "2026-06-09", "2026-06-10"):
        assert (await post(client, emp, body(d))).status_code == 201
    other = (await client.get("/api/v1/me/requests", headers=emp.headers)).json()
    assert [i["start_date"] for i in other["items"]] == ["2026-06-10", "2026-06-09", "2026-06-08"]
    page = (
        await client.get("/api/v1/me/requests", params={"limit": 2}, headers=emp.headers)
    ).json()
    assert len(page["items"]) == 2 and page["next_cursor"]
    rest = (
        await client.get(
            "/api/v1/me/requests",
            params={"limit": 2, "cursor": page["next_cursor"]},
            headers=emp.headers,
        )
    ).json()
    assert len(rest["items"]) == 1 and rest["next_cursor"] is None
    none = await client.get(
        "/api/v1/me/requests", params={"status": "approved"}, headers=emp.headers
    )
    assert none.json()["items"] == []
    assert (
        await client.get("/api/v1/me/requests", params={"status": "x"}, headers=emp.headers)
    ).status_code == 422
    assert (
        await client.get("/api/v1/me/requests", params={"year": 2025}, headers=emp.headers)
    ).json()["items"] == []


async def test_list_never_shows_others(client, staff, make_login) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    await post(client, emp, body())
    assert (await client.get("/api/v1/me/requests", headers=mgr.headers)).json()["items"] == []


# --- preview -------------------------------------------------------------------------------


async def test_preview_writes_nothing_and_reports(client, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    r = await post(client, emp, body("2026-06-08", "2026-06-10"), PREVIEW)
    assert r.status_code == 200
    j = r.json()
    assert j["valid"] and j["working_days"] == 3.0 and j["errors"] == []
    assert j["per_year"] == [
        {"year": 2026, "days": 3.0, "available_before": 12.0, "available_after": 9.0}
    ]
    async with owner_engine.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM leave_request")) == 0
        assert await conn.scalar(text("SELECT count(*) FROM email_outbox")) == 0
        assert await conn.scalar(text("SELECT count(*) FROM audit_log")) == 0


async def test_preview_lists_errors_and_unpaid_has_no_balance(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    bad = (await post(client, emp, body("2026-06-10", "2026-06-09"), PREVIEW)).json()
    assert not bad["valid"] and bad["errors"][0]["field"] == "end_date"
    many = (await post(client, emp, body("2026-05-25", "2026-06-26"), PREVIEW)).json()
    assert {e["code"] for e in many["errors"]} >= {"START_IN_PAST", "INSUFFICIENT_BALANCE"}
    unpaid = (await post(client, emp, body(leave_type="unpaid"), PREVIEW)).json()
    assert unpaid["valid"] and unpaid["per_year"][0]["available_before"] is None


async def test_preview_reports_overlap_and_cross_year(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    await post(client, emp, body("2026-06-08"))
    clash = (await post(client, emp, body("2026-06-08"), PREVIEW)).json()
    assert clash["errors"][0]["code"] == "OVERLAP"
    split = (
        await post(client, emp, body("2026-12-30", "2027-01-05", leave_type="unpaid"), PREVIEW)
    ).json()
    assert [y["year"] for y in split["per_year"]] == [2026, 2027]


async def test_duplicate_reports_overlap_not_insufficient(client, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    await seed_year(owner_engine, emp.employee_id, "entitlement", "1")
    assert (await post(client, emp, body("2026-06-08"))).status_code == 201
    dup = await post(client, emp, body("2026-06-08"))
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "OVERLAP"


async def test_whitespace_note_is_dropped(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    resp = await post(client, emp, body("2026-06-08", note="   "))
    assert resp.status_code == 201 and resp.json()["note"] is None


async def test_cursor_is_stable_when_new_requests_arrive(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    for d in ("2026-06-08", "2026-06-09", "2026-06-10"):
        assert (await post(client, emp, body(d))).status_code == 201
    first = (
        await client.get("/api/v1/me/requests", params={"limit": 2}, headers=emp.headers)
    ).json()
    assert (await post(client, emp, body("2026-06-15"))).status_code == 201
    rest = (
        await client.get(
            "/api/v1/me/requests",
            params={"limit": 2, "cursor": first["next_cursor"]},
            headers=emp.headers,
        )
    ).json()
    assert [i["start_date"] for i in rest["items"]] == ["2026-06-08"]
    bad = await client.get("/api/v1/me/requests", params={"cursor": "zzz"}, headers=emp.headers)
    assert bad.status_code == 422
