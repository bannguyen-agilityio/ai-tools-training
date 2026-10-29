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
from app.modules.audit.router import router as audit_router
from app.spa import mount_spa


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    docs = settings.environment == "dev"
    app = FastAPI(
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

    app.include_router(audit_router)
    mount_spa(app)
    return app


app = create_app()
