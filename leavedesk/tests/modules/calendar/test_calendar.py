import json
import uuid

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login, MakeLogin
from tests.modules.balances.test_ledger_jobs import seed_year
from tests.modules.requests.test_requests import body, post

URL = "/api/v1/calendar"


async def team(owner: AsyncEngine, name: str) -> uuid.UUID:
    tid = uuid.uuid4()
    async with owner.connect() as conn:
        await conn.execute(
            text("INSERT INTO team (id, name) VALUES (:i, :n)"), {"i": tid, "n": f"{name}{tid}"}
        )
    return tid


async def join(owner: AsyncEngine, who: Login, team_id: uuid.UUID | None) -> None:
    async with owner.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET team_id = :t WHERE id = :e"),
            {"t": team_id, "e": who.employee_id},
        )


async def member(
    make_login: MakeLogin, owner: AsyncEngine, team_id: uuid.UUID | None, role: str = "employee"
) -> Login:
    who = await make_login(role)
    await join(owner, who, team_id)
    await seed_year(owner, who.employee_id, "entitlement", "12")
    await seed_year(owner, who.employee_id, "entitlement", "7", type="sick")
    return who


async def book(
    client: httpx.AsyncClient,
    owner: AsyncEngine,
    who: Login,
    start: str,
    end: str | None = None,
    *,
    approved: bool = False,
    **kw: object,
) -> str:
    mgr = await member_manager(owner, who)
    assert mgr
    r = await post(client, who, body(start, end, **kw))
    assert r.status_code == 201, r.text
    rid = str(r.json()["id"])
    if approved:
        async with owner.connect() as conn:
            await conn.execute(
                text("UPDATE leave_request SET status = 'approved' WHERE id = :r"),
                {"r": uuid.UUID(rid)},
            )
    return rid


async def member_manager(owner: AsyncEngine, who: Login) -> bool:
    """Requests need an active manager; give the person one once."""
    async with owner.connect() as conn:
        current = await conn.scalar(
            text("SELECT manager_id FROM employee WHERE id = :e"), {"e": who.employee_id}
        )
        if current is not None:
            return True
        mgr = uuid.uuid4()
        await conn.execute(
            text(
                "INSERT INTO employee (id, name, email, role, start_date, is_active) "
                "VALUES (:i, 'Boss', :m, 'manager', '2026-01-01', true)"
            ),
            {"i": mgr, "m": f"boss{mgr.hex[:8]}@asnet.com.vn"},
        )
        await conn.execute(
            text("UPDATE employee SET manager_id = :m WHERE id = :e"),
            {"m": mgr, "e": who.employee_id},
        )
    return True


async def cal(
    client: httpx.AsyncClient, who: Login, month: str = "2026-06", team_id: object = None
) -> httpx.Response:
    q = f"?month={month}" + (f"&team_id={team_id}" if team_id else "")
    return await client.get(f"{URL}{q}", headers=who.headers)


def entries(r: httpx.Response) -> list[dict]:  # type: ignore[type-arg]
    assert r.status_code == 200, r.text
    return r.json()["entries"]  # type: ignore[no-any-return]


async def test_requires_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(f"{URL}?month=2026-06")).status_code == 401


async def test_bad_month_is_422(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    who = await make_login()
    for month in ("", "2026-13", "2026-6", "june", "2026-06-01", "0000-05", "9999-01"):
        r = await client.get(f"{URL}?month={month}", headers=who.headers)
        assert r.status_code == 422, month


async def test_own_team_only_and_other_team_is_403(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    mine, theirs = await team(owner_engine, "Mine"), await team(owner_engine, "Theirs")
    me = await member(make_login, owner_engine, mine)
    mate = await member(make_login, owner_engine, mine)
    other = await member(make_login, owner_engine, theirs)
    await book(client, owner_engine, mate, "2026-06-08", approved=True)
    await book(client, owner_engine, other, "2026-06-09")

    got = entries(await cal(client, me))
    assert {e["employee_id"] for e in got} == {str(mate.employee_id)}
    assert entries(await cal(client, me, team_id=mine)) == got
    r = await cal(client, me, team_id=theirs)
    assert r.status_code == 403
    assert str(other.employee_id) not in r.text


async def test_manager_and_deputy_are_scoped_to_their_own_team_too(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    mine, theirs = await team(owner_engine, "Mine"), await team(owner_engine, "Theirs")
    mgr = await member(make_login, owner_engine, mine, "manager")
    deputy = await member(make_login, owner_engine, mine)
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :d"), {"d": deputy.employee_id}
        )
    for who in (mgr, deputy):
        assert (await cal(client, who, team_id=theirs)).status_code == 403
        assert (await cal(client, who, team_id=mine)).status_code == 200


async def test_person_without_a_team_sees_nothing(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    loner = await member(make_login, owner_engine, None)
    await book(client, owner_engine, loner, "2026-06-08")
    r = await cal(client, loner)
    assert entries(r) == [] and r.json()["team_id"] is None


async def test_pending_is_distinct_and_cancelled_is_gone(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    t = await team(owner_engine, "T")
    me, mate = await member(make_login, owner_engine, t), await member(make_login, owner_engine, t)
    await book(client, owner_engine, mate, "2026-06-08", approved=True)
    pending = await book(client, owner_engine, mate, "2026-06-09")
    gone = await book(client, owner_engine, mate, "2026-06-10")
    await post(client, mate, {"version": 1}, f"/api/v1/requests/{gone}/cancel")
    got = entries(await cal(client, me))
    assert [(e["date"], e["status"]) for e in got] == [
        ("2026-06-08", "approved"),
        ("2026-06-08", "approved"),
        ("2026-06-09", "pending"),
        ("2026-06-09", "pending"),
    ]
    assert all(e["leave_type"] == "annual" for e in got)
    assert pending not in json.dumps(got)  # entries never carry a request id


async def test_half_days_month_edges_and_other_months(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    t = await team(owner_engine, "T")
    me, mate = await member(make_login, owner_engine, t), await member(make_login, owner_engine, t)
    await book(client, owner_engine, mate, "2026-06-30", start_part="pm", end_part="pm")
    await book(client, owner_engine, mate, "2026-07-01", leave_type="unpaid")
    june = entries(await cal(client, me, "2026-06"))
    assert [(e["date"], e["slot"]) for e in june] == [("2026-06-30", "pm")]
    july = entries(await cal(client, me, "2026-07"))
    assert [(e["date"], e["leave_type"]) for e in july][0] == ("2026-07-01", "unpaid")
    assert entries(await cal(client, me, "2026-08")) == []


async def test_sick_is_masked_identically_for_pending_and_approved(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    t = await team(owner_engine, "T")
    owner_, mate, hr = (
        await member(make_login, owner_engine, t),
        await member(make_login, owner_engine, t),
        await make_login("hr"),
    )
    await book(client, owner_engine, owner_, "2026-06-08", leave_type="sick", approved=True)
    await book(client, owner_engine, owner_, "2026-06-09", leave_type="sick", note="private note")

    raw = (await cal(client, mate)).text
    got = json.loads(raw)["entries"]
    assert len(got) == 4
    for e in got:
        assert set(e) == {"employee_id", "employee_name", "date", "slot", "label"}
        assert e["label"] == "Off"
    assert "sick" not in raw.lower() and "private note" not in raw
    assert "pending" not in raw and "approved" not in raw  # no status at all

    # The owner and HR see the real type and status.
    own = entries(await cal(client, owner_))
    assert {(e["leave_type"], e["status"]) for e in own} == {
        ("sick", "approved"),
        ("sick", "pending"),
    }
    seen_by_hr = entries(await cal(client, hr, team_id=t))
    assert {e["leave_type"] for e in seen_by_hr} == {"sick"}


async def test_hr_sees_all_teams_or_one(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    a, b = await team(owner_engine, "A"), await team(owner_engine, "B")
    ea, eb = await member(make_login, owner_engine, a), await member(make_login, owner_engine, b)
    hr = await make_login("hr")
    await book(client, owner_engine, ea, "2026-06-08")
    await book(client, owner_engine, eb, "2026-06-09", leave_type="unpaid")
    everyone = entries(await cal(client, hr))
    assert {e["employee_id"] for e in everyone} == {str(ea.employee_id), str(eb.employee_id)}
    only_b = entries(await cal(client, hr, team_id=b))
    assert {e["employee_id"] for e in only_b} == {str(eb.employee_id)}


async def test_deactivated_staff_are_hr_only(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    t = await team(owner_engine, "T")
    me, mate = await member(make_login, owner_engine, t), await member(make_login, owner_engine, t)
    hr = await make_login("hr")
    await book(client, owner_engine, mate, "2026-06-08", approved=True)
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_active = false WHERE id = :e"), {"e": mate.employee_id}
        )
    assert entries(await cal(client, me)) == []
    assert len(entries(await cal(client, hr, team_id=t))) == 2
