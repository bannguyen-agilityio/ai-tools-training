from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, Query

from app.core.config import get_settings
from app.modules.holidays.service import MAX_YEAR, MIN_YEAR
from app.modules.identity.dependencies import require_hr
from app.modules.identity.models import Employee

HrUser = Annotated[Employee, Depends(require_hr)]


def current_year() -> int:
    return datetime.now(ZoneInfo(get_settings().company_tz)).year


def year_param(year: Annotated[int | None, Query(ge=MIN_YEAR, le=MAX_YEAR)] = None) -> int:
    return year if year is not None else current_year()


YearParam = Annotated[int, Depends(year_param)]
