import time
import uuid
from datetime import date, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login, MakeLogin

URL = "/api/v1/hr/leave"


async def seed(
    owner: AsyncEngine,
    employee: Login,
    start: date,
    *,
    days: int = 1,
    status: str = "approved",
    leave_type: str = "annual",
    note: str | None = None,
) -> str:
    rid = uuid.uuid4()
    async with owner.connect() as conn:
        await conn.execute(
            text(
                "INSERT INTO leave_request (id, employee_id, leave_type_code, start_date, "
                "start_part, end_date, end_part, working_days, note, status, queue, "
                "decision_reason) VALUES (:id, :e, :t, :s, 'full', :en, 'full', :d, :n, :st, "
                "'manager', :dr)"
            ),
            {
                "id": rid,
                "e": employee.employee_id,
                "t": leave_type,
                "s": start,
                "en": start + timedelta(days=days - 1),
                "d": days,
                "n": note,
                "st": status,
                "dr": "no" if status == "rejected" else None,
            },
        )
    return str(rid)


async def get(client: httpx.AsyncClient, who: Login, query: str = "") -> httpx.Response:
    return await client.get(f"{URL}{query}", headers=who.headers)


def ids(r: httpx.Response) -> list[str]:
    return [i["id"] for i in r.json()["items"]]


async def test_requires_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401


async def test_only_hr_admin_may_list(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    deputy = await make_login()
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :d"), {"d": deputy.employee_id}
        )
    for who in (await make_login(), await make_login("manager"), deputy):
        assert (await get(client, who)).status_code == 403


async def test_defaults_to_approved_and_shows_real_type_and_note(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    ok = await seed(owner_engine, emp, date(2026, 11, 2), leave_type="sick", note="flu")
    pending = await seed(owner_engine, emp, date(2026, 11, 9), status="pending")
    await seed(owner_engine, emp, date(2026, 11, 16), status="rejected")
    await seed(owner_engine, emp, date(2026, 11, 23), status="cancelled")
    r = await get(client, hr)
    assert r.status_code == 200 and ids(r) == [ok]
    row = r.json()["items"][0]
    assert (row["leave_type"], row["note"], row["employee_id"]) == (
        "sick",
        "flu",
        str(emp.employee_id),
    )
    assert ids(await get(client, hr, "?status=pending")) == [pending]


async def test_each_filter_narrows(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, a, b = await make_login("hr"), await make_login(), await make_login()
    async with owner_engine.connect() as conn:
        team = uuid.uuid4()
        await conn.execute(
            text("INSERT INTO team (id, name) VALUES (:t, :n)"), {"t": team, "n": f"T{team}"}
        )
        await conn.execute(
            text("UPDATE employee SET team_id = :t WHERE id = :e"),
            {"t": team, "e": a.employee_id},
        )
    r1 = await seed(owner_engine, a, date(2026, 11, 2), days=3)  # 2-4 Nov
    r2 = await seed(owner_engine, b, date(2026, 11, 10), leave_type="unpaid")
    r3 = await seed(owner_engine, a, date(2026, 12, 1), leave_type="sick")
    assert ids(await get(client, hr)) == [r1, r2, r3]
    assert ids(await get(client, hr, f"?employee_id={b.employee_id}")) == [r2]
    assert ids(await get(client, hr, f"?team_id={team}")) == [r1, r3]
    assert ids(await get(client, hr, "?type=unpaid")) == [r2]
    # A range matches any overlap: 4 Nov touches the last day of r1.
    assert ids(await get(client, hr, "?from=2026-11-04&to=2026-11-30")) == [r1, r2]
    assert ids(await get(client, hr, "?from=2026-11-05&to=2026-11-30")) == [r2]
    both = f"?team_id={team}&type=sick&from=2026-11-01&to=2026-12-31"
    assert ids(await get(client, hr, both)) == [r3]


async def test_bad_filters_are_422(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    for q in (
        "?status=bogus",
        "?type=bogus",
        "?from=nope",
        "?limit=0",
        "?limit=201",
        "?cursor=junk",
        "?from=2026-11-05&to=2026-11-01",
        "?employee_id=x",
    ):
        assert (await get(client, hr, q)).status_code == 422, q


async def test_cursor_walks_every_row_once(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    want = [await seed(owner_engine, emp, date(2026, 11, 2)) for _ in range(3)]  # same day
    want += [await seed(owner_engine, emp, date(2026, 11, 3 + i)) for i in range(4)]
    seen: list[str] = []
    cursor = ""
    while True:
        r = await get(client, hr, f"?limit=2{cursor}")
        seen += ids(r)
        nxt = r.json()["next_cursor"]
        if not nxt:
            break
        cursor = f"&cursor={nxt}"
    assert len(seen) == 7 and set(seen) == set(want) and len(set(seen)) == 7
    starts = [i["start_date"] for i in (await get(client, hr, "?limit=200")).json()["items"]]
    assert starts == sorted(starts)


async def test_two_thousand_rows_page_fast(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    async with owner_engine.connect() as conn:
        await conn.execute(
            text(
                "INSERT INTO leave_request (employee_id, leave_type_code, start_date, start_part, "
                "end_date, end_part, working_days, status, queue) "
                "SELECT :e, 'annual', date '2026-01-01' + (g % 300), 'full', "
                "date '2026-01-01' + (g % 300), 'full', 1, 'approved', 'manager' "
                "FROM generate_series(1, 2000) g"
            ),
            {"e": emp.employee_id},
        )
    started = time.perf_counter()
    r = await get(client, hr, "?limit=200&from=2026-03-01&to=2026-06-30")
    elapsed = time.perf_counter() - started
    assert r.status_code == 200 and len(r.json()["items"]) == 200
    assert elapsed < 0.5, elapsed
