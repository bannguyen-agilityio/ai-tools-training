"""Configure the FastAPI application."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.security import generate_salt, hash_password
from app.infrastructure.database import Base, async_session_factory, engine
from app.modules.auth.models import User


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Create database tables on startup and seed the admin user."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            salt = generate_salt()
            session.add(
                User(
                    username="admin",
                    password_hash=hash_password("admin123", salt),
                    salt=salt,
                    full_name="Admin User",
                )
            )
            await session.commit()

    yield

    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_error_handlers(app)
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    """Return a welcome message with login instructions."""
    return {"message": "Use POST /api/v1/auth/login to log in"}
