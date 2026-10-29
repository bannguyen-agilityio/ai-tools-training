from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(
    url: str | None = None, *, set_role: bool | None = None, **engine_kwargs: Any
) -> AsyncEngine:
    settings = get_settings()
    # Pooled (pgbouncer) URLs do not support server-side prepared statements.
    connect_args: dict[str, Any] = {"prepare_threshold": None}
    if settings.set_role_on_connect if set_role is None else set_role:
        if not settings.app_db_role.isidentifier():
            raise ValueError("APP_DB_ROLE is not a valid role name")
        connect_args["options"] = f"-c role={settings.app_db_role}"
    return create_async_engine(
        url or settings.database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
        **engine_kwargs,
    )


_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(make_engine(), expire_on_commit=False)
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session
