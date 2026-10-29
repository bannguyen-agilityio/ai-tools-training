import httpx

from app.core.csrf import hash_token, new_token, tokens_match
from tests.conftest import MakeLogin


def test_token_helpers() -> None:
    token = new_token()
    assert token != new_token()
    assert tokens_match(token, hash_token(token))
    assert not tokens_match("other", hash_token(token))
    assert not tokens_match(None, hash_token(token))
    assert not tokens_match("", hash_token(token))


async def test_foreign_origin_is_403_even_with_valid_csrf(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.post(
        "/api/v1/_probe",
        json={"name": "a"},
        headers={**u.mutating_headers, "Origin": "https://evil.example"},
    )
    assert r.status_code == 403


async def test_same_origin_passes(pclient: httpx.AsyncClient, make_login: MakeLogin) -> None:
    u = await make_login()
    r = await pclient.post(
        "/api/v1/_probe",
        json={"name": "a"},
        headers={**u.mutating_headers, "Origin": "http://testserver"},
    )
    assert r.status_code == 200


async def test_https_origin_matching_host_passes_behind_tls_proxy(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.post(
        "/api/v1/_probe",
        json={"name": "a"},
        headers={**u.mutating_headers, "Origin": "https://testserver"},
    )
    assert r.status_code == 200


async def test_foreign_origin_is_refused_on_public_routes_too(client: httpx.AsyncClient) -> None:
    r = await client.post("/healthz", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
