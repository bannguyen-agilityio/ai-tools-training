import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.auth import passwords, service
from app.modules.auth.passwords import DUMMY_HASH
from tests.modules.auth.conftest import PASSWORD, MakeUser

URL = "/api/v1/auth/login"
GENERIC = "Email or password is incorrect"


async def test_login_sets_cookie_and_me_works(client: httpx.AsyncClient, make_user: MakeUser):
    u = await make_user()
    r = await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "session=" in cookie
    me = await client.get("/api/v1/me")
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == u.email and body["role"] == "employee"
    assert body["is_hr_deputy"] is False and body["api_version"] == "v1"
    assert body["csrf_token"] == r.json()["csrf_token"]


async def test_csrf_from_login_works_on_logout(client: httpx.AsyncClient, make_user: MakeUser):
    u = await make_user()
    r = await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert (await client.post("/api/v1/auth/logout")).status_code == 403
    out = await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": r.json()["csrf_token"]})
    assert out.status_code == 204
    assert (await client.get("/api/v1/me")).status_code == 401


async def test_wrong_and_unknown_are_identical(client: httpx.AsyncClient, make_user: MakeUser):
    u = await make_user()
    wrong = await client.post(URL, json={"email": u.email, "password": "nope-nope-nope-1"})
    unknown = await client.post(
        URL, json={"email": "x@asnet.com.vn", "password": "nope-nope-nope-1"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.content == unknown.content
    assert GENERIC in wrong.text


@pytest.mark.parametrize("state", ["inactive", "no_password"])
async def test_inactive_or_uninvited_is_generic(
    client: httpx.AsyncClient, make_user: MakeUser, state: str
):
    u = await make_user(
        active=state != "inactive", password=None if state == "no_password" else PASSWORD
    )
    r = await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert r.status_code == 401 and GENERIC in r.text


async def test_unknown_email_still_verifies_against_dummy_hash(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    seen: list[str] = []
    real = passwords.verify_password

    def spy(hash_: str, pw: str) -> bool:
        seen.append(hash_)
        return real(hash_, pw)

    monkeypatch.setattr("app.modules.auth.service.verify_password", spy)
    await client.post(URL, json={"email": "ghost@asnet.com.vn", "password": "whatever-123456"})
    assert seen == [DUMMY_HASH]


async def test_login_rotates_existing_session(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user()
    await client.post(URL, json={"email": u.email, "password": PASSWORD})
    first = client.cookies["session"]
    await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert client.cookies["session"] != first
    async with owner_engine.connect() as c:
        n = await c.scalar(text("SELECT count(*) FROM session WHERE employee_id=:e"), {"e": u.id})
    assert n == 1


async def test_strict_body(client: httpx.AsyncClient):
    r = await client.post(URL, json={"email": "a@asnet.com.vn", "password": "x", "admin": True})
    assert r.status_code == 422


async def test_non_company_email_rejected_by_db(owner_engine: AsyncEngine):
    with pytest.raises(Exception, match="ck_employee_email_domain"):
        async with owner_engine.connect() as c:
            await c.execute(
                text(
                    "INSERT INTO employee (name,email,start_date) "
                    "VALUES ('a','a@gmail.com','2026-01-01')"
                )
            )


def test_service_refuses_other_domain():
    with pytest.raises(service.InvalidEmailDomain):
        service.require_company_email("a@gmail.com")
