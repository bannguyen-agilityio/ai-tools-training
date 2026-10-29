import os
import subprocess
import sys

from scripts import check_single_head

APP_SETTINGS = (
    "ENVIRONMENT",
    "DATABASE_URL",
    "APP_DB_ROLE",
    "COMPANY_TZ",
    "EMAIL_BACKEND",
    "APP_BASE_URL",
)


def test_repository_has_a_single_head(capsys) -> None:  # type: ignore[no-untyped-def]
    assert check_single_head.main() == 0
    assert "single Alembic head" in capsys.readouterr().out


def test_script_runs_without_any_app_configuration() -> None:
    """CI and deploys run it before any database or settings exist."""
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {*APP_SETTINGS, "ENV_FILE", "MIGRATION_DATABASE_URL", "COOKIE_SECURE"}
    }
    result = subprocess.run(
        [sys.executable, "scripts/check_single_head.py"], capture_output=True, text=True, env=env
    )
    assert result.returncode == 0, result.stdout + result.stderr
