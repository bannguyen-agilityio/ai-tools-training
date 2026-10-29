import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.core.deps import PUBLIC_PATHS
from app.core.schemas import StrictModel
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import Employee
from tests.conftest import Login


class Probe(StrictModel):
    name: str


@pytest.fixture
def probe_app(app: FastAPI) -> FastAPI:
    """Adds throwaway routes that exercise the baseline (CSRF, strict body, 500)."""

    @app.post("/api/v1/_probe")
    def probe(body: Probe, user: Annotated[Employee, Depends(get_current_user)]) -> dict[str, str]:
        return {"name": body.name}

    @app.get("/api/v1/_boom")
    def boom(user: Annotated[Employee, Depends(get_current_user)]) -> None:
        raise RuntimeError("secret-internal-detail")

    return app


@pytest.fixture
def pclient(probe_app: FastAPI) -> TestClient:
    return TestClient(probe_app, raise_server_exceptions=False)


def _concrete(path: str) -> str:
    out = path
    while "{" in out:
        start, end = out.index("{"), out.index("}")
        out = out[:start] + str(uuid.uuid4()) + out[end + 1 :]
    return out


# R29a
def test_every_non_public_route_returns_401_without_session(pclient: TestClient) -> None:
    checked = 0
    # openapi() lists every operation, including routers nested via include_router.
    for path, operations in pclient.app.openapi()["paths"].items():  # type: ignore[attr-defined]
        if path in PUBLIC_PATHS:
            continue
        for method in operations:
            r = pclient.request(method.upper(), _concrete(path), json={})
            assert r.status_code == 401, f"{method.upper()} {path} -> {r.status_code}"
            assert r.headers["content-type"].startswith("application/problem+json")
            checked += 1
    assert checked >= 3


def test_garbage_and_expired_sessions_are_401(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    assert pclient.get("/api/v1/audit-log", cookies={"session": "nope"}).status_code == 401
    expired = make_login("hr", expires_in=timedelta(seconds=-1))
    assert pclient.get("/api/v1/audit-log", cookies=expired.cookies).status_code == 401


def test_deactivated_employee_session_is_401(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    gone = make_login("hr", active=False)
    assert pclient.get("/api/v1/audit-log", cookies=gone.cookies).status_code == 401


def test_healthz_is_public_and_minimal(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_authorization_is_enforced_per_role(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    emp, hr = make_login("employee"), make_login("hr")
    assert pclient.get("/api/v1/audit-log", cookies=emp.cookies).status_code == 403
    assert pclient.get("/api/v1/audit-log", cookies=hr.cookies).status_code == 200


# R29c
def test_post_without_csrf_token_is_403(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    u = make_login()
    r = pclient.post("/api/v1/_probe", json={"name": "a"}, cookies=u.cookies)
    assert r.status_code == 403


def test_post_with_wrong_csrf_token_is_403(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    u = make_login()
    r = pclient.post(
        "/api/v1/_probe", json={"name": "a"}, cookies=u.cookies, headers={"X-CSRF-Token": "x"}
    )
    assert r.status_code == 403


def test_foreign_origin_is_403_even_with_valid_csrf(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    u = make_login()
    r = pclient.post(
        "/api/v1/_probe",
        json={"name": "a"},
        cookies=u.cookies,
        headers={**u.headers, "Origin": "https://evil.example"},
    )
    assert r.status_code == 403


def test_valid_csrf_and_same_origin_passes(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    u = make_login()
    r = pclient.post(
        "/api/v1/_probe",
        json={"name": "a"},
        cookies=u.cookies,
        headers={**u.headers, "Origin": "http://testserver"},
    )
    assert r.status_code == 200
    assert r.json() == {"name": "a"}


def test_https_origin_matching_host_passes_behind_tls_proxy(pclient: TestClient, make_login):
    u = make_login()
    r = pclient.post(
        "/api/v1/_probe",
        json={"name": "a"},
        cookies=u.cookies,
        headers={**u.headers, "Origin": "https://testserver"},
    )
    assert r.status_code == 200


def test_csrf_not_required_for_get(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    hr = make_login("hr")
    assert pclient.get("/api/v1/audit-log", cookies=hr.cookies).status_code == 200


# R29b
def test_unknown_field_is_refused_without_echoing_values(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    u: Login = make_login()
    r = pclient.post(
        "/api/v1/_probe",
        json={"name": "a", "role": "hr-secret-value"},
        cookies=u.cookies,
        headers=u.headers,
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert "hr-secret-value" not in r.text


def test_sql_metacharacters_are_data_not_sql(
    pclient: TestClient, make_login, owner_engine: Engine
) -> None:  # type: ignore[no-untyped-def]
    u = make_login("hr")
    evil = "x'; DROP TABLE employee;--"
    r = pclient.get("/api/v1/audit-log", params={"limit": evil}, cookies=u.cookies)
    assert r.status_code == 422
    with owner_engine.connect() as conn:
        assert conn.scalar(text("SELECT count(*) FROM employee")) == 1


# R29d
def test_security_headers_present(client: TestClient) -> None:
    h = client.get("/healthz").headers
    assert "default-src 'self'" in h["content-security-policy"]
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"]
    assert "max-age=" in h["strict-transport-security"]


def test_security_headers_on_error_responses(client: TestClient) -> None:
    r = client.get("/api/v1/audit-log")
    assert r.status_code == 401
    assert r.headers["x-content-type-options"] == "nosniff"


def test_unhandled_exception_is_generic_problem_json(pclient: TestClient, make_login) -> None:  # type: ignore[no-untyped-def]
    u = make_login()
    r = pclient.get("/api/v1/_boom", cookies=u.cookies)
    assert r.status_code == 500
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["status"] == 500
    assert "secret-internal-detail" not in r.text
    assert "Traceback" not in r.text


def test_not_found_is_problem_json(client: TestClient) -> None:
    r = client.get("/nope")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")


def test_docs_are_not_exposed_outside_dev(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


# R2 sliding window
def test_session_expiry_slides_but_is_capped_at_24h(
    pclient: TestClient, make_login, owner_engine: Engine
) -> None:  # type: ignore[no-untyped-def]
    u = make_login("hr", age=timedelta(hours=20), expires_in=timedelta(hours=1))
    assert pclient.get("/api/v1/audit-log", cookies=u.cookies).status_code == 200
    with owner_engine.connect() as conn:
        created, expires = conn.execute(
            text("SELECT created_at, expires_at FROM session WHERE employee_id = :e"),
            {"e": u.employee_id},
        ).one()
    assert expires == created + timedelta(hours=24)
    assert expires > datetime.now(UTC) + timedelta(hours=3)


def test_production_refuses_mock_email() -> None:
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(environment="production", email_backend="mock")
