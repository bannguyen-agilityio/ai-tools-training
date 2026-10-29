import httpx

from tests.conftest import MakeLogin


async def test_unhandled_exception_is_generic_problem_json(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.get("/api/v1/_boom", headers=u.headers)
    assert r.status_code == 500
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["status"] == 500
    assert "secret-internal-detail" not in r.text
    assert "Traceback" not in r.text


async def test_not_found_is_problem_json(client: httpx.AsyncClient) -> None:
    r = await client.get("/nope")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")


async def test_validation_error_is_422_problem_json_without_echo(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.post(
        "/api/v1/_probe",
        json={"name": "a", "role": "hr-secret-value"},
        headers=u.mutating_headers,
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert "hr-secret-value" not in r.text
