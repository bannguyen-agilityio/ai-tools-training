from typing import Annotated

from fastapi import Depends

from app.modules.identity.dependencies import require_hr
from app.modules.identity.models import Employee

HrUser = Annotated[Employee, Depends(require_hr)]
