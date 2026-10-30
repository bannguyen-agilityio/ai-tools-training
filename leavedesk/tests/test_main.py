import uuid

import httpx
from fastapi import FastAPI

from app.core.deps import PUBLIC_PATHS


def _concrete(path: str) -> str:
    out = path
    while "{" in out:
        start, end = out.index("{"), out.index("}")
        out = out[:start] + str(uuid.uuid4()) + out[end + 1 :]
    return out


# R29a
async def test_every_non_public_route_returns_401_without_session(
    probe_app: FastAPI, pclient: httpx.AsyncClient
) -> None:
    checked = 0
    # openapi() lists every operation, including routers nested via include_router.
    for path, operations in probe_app.openapi()["paths"].items():
        if path in PUBLIC_PATHS:
            continue
        for method in operations:
            r = await pclient.request(method.upper(), _concrete(path), json={})
            assert r.status_code == 401, f"{method.upper()} {path} -> {r.status_code}"
            assert r.json()["error"]["code"] == "UNAUTHENTICATED"
            checked += 1
    assert checked >= 3


async def test_healthz_is_public_and_minimal(client: httpx.AsyncClient) -> None:
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_docs_are_not_exposed_outside_dev(client: httpx.AsyncClient) -> None:
    assert (await client.get("/docs")).status_code == 404
    assert (await client.get("/openapi.json")).status_code == 404
