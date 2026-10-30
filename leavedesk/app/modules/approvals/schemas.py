import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from app.core.schemas import StrictModel
from app.modules.requests.schemas import RequestOut


class ApproveIn(StrictModel):
    version: int = Field(ge=1)
    # Cover (R20): the request's direct manager, whom the caller stands in for.
    on_behalf_of: uuid.UUID | None = None


def _trim(value: str) -> str:
    return value.strip()


class RejectIn(StrictModel):
    version: int = Field(ge=1)
    on_behalf_of: uuid.UUID | None = None
    # Trimmed after the type check but length-checked by the second annotation, so a
    # whitespace-only reason fails min_length (R19).
    reason: Annotated[str, AfterValidator(_trim), Field(min_length=1, max_length=500)]


class ApprovalList(BaseModel):
    items: list[RequestOut]
