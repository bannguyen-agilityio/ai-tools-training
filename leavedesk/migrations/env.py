import asyncio
import os

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import app.modules.audit.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
from app.core.config import get_settings
from app.core.db import Base

target_metadata = Base.metadata


def _url() -> str:
    # Migrations run as the owner (MIGRATION_DATABASE_URL), not the restricted app role.
    return os.environ.get("MIGRATION_DATABASE_URL") or get_settings().database_url


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(_url())
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


asyncio.run(run_migrations_online())
