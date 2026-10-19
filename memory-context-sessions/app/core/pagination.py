"""Shared pagination primitives for list endpoints."""

import math
from dataclasses import dataclass

from fastapi import Query
from pydantic import BaseModel, Field


@dataclass
class PaginationParams:
    """Query parameters for paginated list endpoints."""

    page: int = Query(default=1, ge=1)
    page_size: int = Query(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Compute the SQL offset from page and page_size."""
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseModel):
    """Pagination metadata included in paginated responses."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    next_page: int | None = None
    prev_page: int | None = None


class PaginatedResponse[T](BaseModel):
    """Paginated list response wrapping items and metadata."""

    items: list[T]
    meta: PaginationMeta


def build_pagination_meta(
    *, page: int, page_size: int, total_items: int
) -> PaginationMeta:
    """Compute pagination metadata from the current page and total count.

    Args:
        page: The current page number (1-indexed).
        page_size: The number of items per page.
        total_items: The total number of matching items.

    Returns:
        A populated PaginationMeta instance.
    """
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None,
    )
