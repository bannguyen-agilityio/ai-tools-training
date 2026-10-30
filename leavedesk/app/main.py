import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.csrf import OriginCheckMiddleware
from app.core.db import get_db
from app.core.errors import ProblemError, install_error_handlers
from app.core.logging import configure_logging
from app.core.security_headers import SecurityHeadersMiddleware
from app.jobs.drain_outbox import run_forever
from app.modules.approvals.router import router as approvals_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.balances.hr_router import router as balances_router
from app.modules.balances.me_router import router as me_balances_router
from app.modules.email.router import router as email_router
from app.modules.employees.router import router as employees_router
from app.modules.holidays.router import router as holidays_router
from app.modules.notifications.router import router as notifications_router
from app.modules.reports.router import router as reports_router
from app.modules.requests.hr_router import router as hr_requests_router
from app.modules.requests.router import router as requests_router
from app.modules.teams.router import router as teams_router
from app.spa import mount_spa


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # In-process outbox drain every minute; the CI job is the backstop (spec §5.6).
    task = asyncio.create_task(run_forever())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    docs = settings.environment == "dev"
    app = FastAPI(
        lifespan=lifespan,
        title="LeaveDesk",
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    install_error_handlers(app)
    app.add_middleware(OriginCheckMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/healthz")
    async def healthz(db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
        try:
            await db.execute(text("SELECT 1"))
        except Exception as exc:
            raise ProblemError(503, "Database unavailable") from exc
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(audit_router)
    app.include_router(balances_router)
    app.include_router(me_balances_router)
    app.include_router(email_router)
    app.include_router(employees_router)
    app.include_router(holidays_router)
    app.include_router(teams_router)
    app.include_router(notifications_router)
    app.include_router(reports_router)
    app.include_router(requests_router)
    app.include_router(hr_requests_router)
    app.include_router(approvals_router)
    mount_spa(app)  # last: it serves the catch-all for client routes
    return app


app = create_app()
