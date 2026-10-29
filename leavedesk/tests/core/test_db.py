import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.db import make_engine


async def test_app_engine_runs_as_restricted_role(app_engine: AsyncEngine, app_role: str) -> None:
    async with app_engine.connect() as conn:
        assert await conn.scalar(text("SELECT current_user")) == app_role
        is_super = await conn.scalar(
            text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        )
    assert is_super is False


async def test_engine_is_async_and_disables_prepared_statements(app_engine: AsyncEngine) -> None:
    async with app_engine.connect() as conn:
        assert await conn.scalar(text("SELECT 1")) == 1


def test_invalid_role_name_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import config

    monkeypatch.setattr(config.get_settings(), "app_db_role", "x; DROP ROLE y")
    with pytest.raises(ValueError):
        make_engine(set_role=True)
