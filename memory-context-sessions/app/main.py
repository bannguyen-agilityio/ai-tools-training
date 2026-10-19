"""Configure the FastAPI application."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.security import generate_salt, hash_password
from app.infrastructure.database import Base, async_session_factory, engine
from app.modules.auth.models import User

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Create database tables on startup and seed the initial user."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _seed_initial_user()

    yield

    await engine.dispose()


async def _seed_initial_user() -> None:
    """Create the seed user if it does not already exist.

    Handles the race condition where multiple workers try to
    insert simultaneously by catching IntegrityError.
    """
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.username == settings.seed_username)
        )
        if result.scalar_one_or_none():
            return

        salt = generate_salt()
        session.add(
            User(
                username=settings.seed_username,
                password_hash=hash_password(settings.seed_password, salt),
                salt=salt,
                full_name=settings.seed_full_name,
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            logger.info(
                "Seed user '%s' already created by another worker",
                settings.seed_username,
            )


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_error_handlers(app)
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    """Return a welcome message with login instructions."""
    return {"message": "Use POST /api/v1/auth/login to log in"}
