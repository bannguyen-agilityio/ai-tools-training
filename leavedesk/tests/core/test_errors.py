import httpx
import pytest

from app.core import errors
from tests.conftest import MakeLogin


class _Settings:
    def __init__(self, environment: str) -> None:
        self.environment = environment


async def test_unhandled_exception_is_the_envelope_with_stack_outside_production(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.get("/api/v1/_boom", headers=u.headers)
    assert r.status_code == 500
    assert r.headers["content-type"].startswith("application/json")
    error = r.json()["error"]
    assert error["code"] == "INTERNAL_ERROR"
    assert "details" not in error
    assert "Traceback" in error["stack"]  # ENVIRONMENT=test


@pytest.mark.parametrize("environment", ["production"])
async def test_stack_is_never_returned_in_production(
    pclient: httpx.AsyncClient,
    make_login: MakeLogin,
    monkeypatch: pytest.MonkeyPatch,
    environment: str,
) -> None:
    u = await make_login()
    monkeypatch.setattr(errors, "get_settings", lambda: _Settings(environment))
    for r in (
        await pclient.get("/api/v1/_boom", headers=u.headers),  # 5xx
        await pclient.get("/api/v1/nope"),  # 404
        await pclient.post("/api/v1/_probe", json={}, headers=u.mutating_headers),  # 422
        await pclient.get("/api/v1/_probe", headers=u.headers),  # 405
    ):
        assert r.status_code >= 400
        assert "stack" not in r.json()["error"]
        assert "Traceback" not in r.text
        assert "secret-internal-detail" not in r.text


async def test_not_found_is_the_envelope(client: httpx.AsyncClient) -> None:
    for path in ("/api/v1/nope", "/api/v9/anything"):
        r = await client.get(path)
        assert r.status_code == 404
        assert r.json() == {"error": {"code": "NOT_FOUND", "message": "Not Found"}}


async def test_validation_error_has_details_and_does_not_echo_values(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.post("/api/v1/_probe", json={}, headers=u.mutating_headers)
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"] == [{"field": "body.name", "issue": "Field required"}]


async def test_unknown_fields_are_400_without_echo(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.post(
        "/api/v1/_probe",
        json={"name": "a", "role": "hr-secret-value"},
        headers=u.mutating_headers,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert r.json()["error"]["details"][0]["field"] == "body.role"
    assert "hr-secret-value" not in r.text


async def test_problem_error_carries_a_stable_code(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr = await make_login("hr")
    dup = await client.post(
        "/api/v1/hr/holidays",
        json={"holiday_date": "2026-09-02", "name": "Again"},
        headers=hr.mutating_headers,
    )
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "CONFLICT"
