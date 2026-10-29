import pytest
from pydantic import ValidationError

from app.core.config import Settings

REQUIRED = {
    "environment": "dev",
    "database_url": "postgresql+psycopg://x@h/db",
    "app_db_role": "r",
    "company_tz": "Asia/Ho_Chi_Minh",
    "email_backend": "mock",
    "cookie_secure": False,
}


def test_production_refuses_mock_email() -> None:
    with pytest.raises(ValidationError):
        Settings(**{**REQUIRED, "environment": "production"})  # type: ignore[arg-type]


def test_deployment_values_have_no_code_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DATABASE_URL", "ENVIRONMENT", "APP_DB_ROLE", "COMPANY_TZ"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)  # type: ignore[call-arg]
    missing = {e["loc"][0] for e in exc.value.errors()}
    assert {"database_url", "environment", "app_db_role", "company_tz"} <= missing


def test_values_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPANY_TZ", "UTC")
    assert Settings().company_tz == "UTC"  # type: ignore[call-arg]


def test_values_load_from_env_file(tmp_path: pytest.TempPathFactory, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    for name in REQUIRED:
        monkeypatch.delenv(name.upper(), raising=False)
    env_file = tmp_path / "x.env"  # type: ignore[operator]
    env_file.write_text(
        "ENVIRONMENT=staging\nDATABASE_URL=postgresql+psycopg://u@h/d\nAPP_DB_ROLE=app\n"
        "COMPANY_TZ=Asia/Ho_Chi_Minh\nEMAIL_BACKEND=sendgrid\nCOOKIE_SECURE=true\n"
    )
    s = Settings(_env_file=str(env_file))  # type: ignore[call-arg]
    assert s.environment == "staging"
    assert s.cookie_secure is True
