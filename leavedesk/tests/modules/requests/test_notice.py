from datetime import date
from decimal import Decimal

from fastapi import FastAPI
from sqlalchemy import text

from app.modules.balances.me_router import get_today
from app.modules.requests.notice import Notice, notice_check
from tests.modules.balances.test_ledger_jobs import seed_year
from tests.modules.requests import test_requests as base
from tests.modules.requests.test_requests import PREVIEW, TODAY, body, post

# Reuse the module fixtures (frozen "today", employee with a manager and balance).
fixed_today = base.fixed_today
staff = base.staff

HR_CREATE = "/api/v1/hr/requests"


def check(start: str, end: str, days: str, exempt: bool = False) -> Notice:
    return notice_check(
        exempt=exempt,
        start=date.fromisoformat(start),
        end=date.fromisoformat(end),
        working_days=Decimal(days),
        today=TODAY,
    )


def test_single_day_needs_one_day() -> None:
    assert check("2026-06-01", "2026-06-01", "1") is Notice.BLOCK
    assert check("2026-06-02", "2026-06-02", "1") is Notice.OK
    assert check("2026-06-01", "2026-06-01", "0.5") is Notice.BLOCK


def test_long_request_warns_inside_a_week() -> None:
    assert check("2026-06-04", "2026-06-11", "6") is Notice.WARNING
    assert check("2026-06-08", "2026-06-15", "6") is Notice.OK  # 7 days ahead
    assert check("2026-06-02", "2026-06-04", "3") is Notice.OK  # 2-5 days: no rule
    assert check("2026-06-02", "2026-06-08", "5") is Notice.OK


def test_exempt_skips_everything() -> None:
    assert check("2026-06-01", "2026-06-01", "1", exempt=True) is Notice.OK
    assert check("2026-06-02", "2026-06-12", "9", exempt=True) is Notice.OK


async def test_block_and_ok_over_http(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    blocked = await post(client, emp, body("2026-06-01"))
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "NOTICE_TOO_SHORT"
    assert blocked.json()["error"]["details"][0]["field"] == "start_date"
    assert (await post(client, emp, body("2026-06-02"))).status_code == 201
    unpaid = await post(client, emp, body("2026-06-01", leave_type="unpaid"))
    assert unpaid.status_code == 422


async def test_warning_stored_and_previewed(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    pre = await post(client, emp, body("2026-06-04", "2026-06-11"), PREVIEW)
    assert pre.json()["valid"] is True and pre.json()["notice_warning"] is True
    made = await post(client, emp, body("2026-06-04", "2026-06-11"))
    assert made.status_code == 201 and made.json()["notice_warning"] is True
    far = await post(client, emp, body("2026-06-22", "2026-06-30", leave_type="unpaid"))
    assert far.json()["notice_warning"] is False
    short = await post(client, emp, body("2026-06-16", "2026-06-18", leave_type="unpaid"))
    assert short.json()["notice_warning"] is False


async def test_sick_backdate_window(client, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    await seed_year(owner_engine, emp.employee_id, "entitlement", "7", type="sick")
    for start in ("2026-06-01", "2026-05-25"):  # today, 7 days back (Mon)
        assert (await post(client, emp, body(start, leave_type="sick"))).status_code == 201
    old = await post(client, emp, body("2026-05-22", leave_type="sick"))  # 10 days back
    assert old.status_code == 422 and old.json()["error"]["code"] == "START_IN_PAST"


async def test_midnight_uses_company_timezone(app: FastAPI) -> None:
    from datetime import UTC, datetime
    from unittest.mock import patch

    app.dependency_overrides.pop(get_today, None)
    # 23:30 UTC on 1 Jun is 06:30 on 2 Jun in Vietnam.
    fake = datetime(2026, 6, 1, 23, 30, tzinfo=UTC)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def]
            return fake.astimezone(tz)

    with patch("app.modules.balances.me_router.datetime", Clock):
        assert get_today() == date(2026, 6, 2)


async def test_hr_entry_older_sick(client, staff, make_login, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    hr = await make_login("hr")
    await seed_year(owner_engine, emp.employee_id, "entitlement", "7", type="sick")
    payload = body(
        "2026-05-22", leave_type="sick", employee_id=str(emp.employee_id), entry_reason="Called in"
    )
    resp = await post(client, hr, payload, HR_CREATE)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["employee_id"] == str(emp.employee_id) and data["status"] == "pending"
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT entered_by, entry_reason, assigned_to FROM leave_request")
            )
        ).one()
        audit = str(
            (await conn.execute(text("SELECT actor_id, action, detail FROM audit_log"))).all()
        )
    assert (row[0], row[1], row[2]) == (hr.employee_id, "Called in", mgr.employee_id)
    assert "request.hr_create" in audit and str(hr.employee_id) in audit
    assert "Called in" not in audit and "sick" not in audit.lower()


async def test_hr_entry_validation_and_authz(client, staff, make_login, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    hr = await make_login("hr")
    ok = body("2026-05-22", leave_type="sick", employee_id=str(emp.employee_id))
    assert (await client.post(HR_CREATE, json={**ok, "entry_reason": "x"})).status_code == 401
    deputy = await make_login("manager")
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :i"),
            {"i": deputy.employee_id},
        )
    for who in (emp, mgr, deputy):
        resp = await post(client, who, {**ok, "entry_reason": "x"}, HR_CREATE)
        assert resp.status_code == 403
    for reason in (None, "", "   ", "x" * 501):
        payload = {**ok} if reason is None else {**ok, "entry_reason": reason}
        assert (await post(client, hr, payload, HR_CREATE)).status_code == 422
    own = {**ok, "employee_id": str(hr.employee_id), "entry_reason": "x"}
    assert (await post(client, hr, own, HR_CREATE)).status_code == 403
    ghost = {**ok, "employee_id": "00000000-0000-0000-0000-000000000001", "entry_reason": "x"}
    assert (await post(client, hr, ghost, HR_CREATE)).status_code == 404


async def test_hr_entry_only_backdates_sick(client, staff, make_login) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    hr = await make_login("hr")
    payload = body("2026-05-22", employee_id=str(emp.employee_id), entry_reason="Forgot")
    resp = await post(client, hr, payload, HR_CREATE)
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "START_IN_PAST"


async def test_past_single_day_reports_one_error(client, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    pre = await post(client, emp, body("2026-05-29"), PREVIEW)
    assert [e["code"] for e in pre.json()["errors"]] == ["START_IN_PAST"]
