from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.audit import service as audit
from app.modules.auth.router import client_ip
from app.modules.employees.dependencies import HrUser
from app.modules.reports import service, writers

router = APIRouter(prefix="/api/v1/hr/reports", tags=["reports"])
DB = Annotated[AsyncSession, Depends(get_db)]
Month = Annotated[str, Query(pattern=r"^(19|20)\d{2}-(0[1-9]|1[0-2])$")]

MEDIA = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


@router.get("/monthly")
async def monthly_report(
    request: Request,
    user: HrUser,
    db: DB,
    month: Month,
    format: Literal["xlsx", "csv"] = "xlsx",  # noqa: A002
) -> Response:
    report = await service.build(db, user, month)
    # Rendering is CPU-bound, so it runs off the event loop.
    body = await run_in_threadpool(writers.to_csv if format == "csv" else writers.to_xlsx, report)
    # Who, month, format and size only: never names, types or notes (R30).
    await audit.record(
        db,
        actor_id=user.id,
        action="report.export",
        target_type="report",
        target_id=f"monthly-{month}",
        detail={"month": month, "format": format, "count": len(report.off)},
        ip=client_ip(request),
    )
    await db.commit()
    return Response(
        content=body,
        media_type=MEDIA[format],
        headers={
            "Content-Disposition": f'attachment; filename="leave-report-{month}.{format}"',
            "Cache-Control": "no-store",
            "X-Confidential": "HR only",
        },
    )
