import httpx


async def test_security_headers_present(client: httpx.AsyncClient) -> None:
    h = (await client.get("/healthz")).headers
    assert "default-src 'self'" in h["content-security-policy"]
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"]
    assert "max-age=" in h["strict-transport-security"]


async def test_security_headers_on_error_responses(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/v1/audit-log")
    assert r.status_code == 401
    assert r.headers["x-content-type-options"] == "nosniff"
