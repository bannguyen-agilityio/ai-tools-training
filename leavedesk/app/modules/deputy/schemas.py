import uuid

from pydantic import BaseModel

from app.core.schemas import StrictModel


class DeputyOut(BaseModel):
    """The one deputy, or `employee_id: null` when none is set."""

    employee_id: uuid.UUID | None
    name: str | None = None
    email: str | None = None


class DeputyIn(StrictModel):
    employee_id: uuid.UUID | None
