from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int = Field(..., description="Total number of matching records")
    page: PositiveInt = Field(..., description="Current page number")
    page_size: PositiveInt = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


def calculate_pages(total: NonNegativeInt, page_size: PositiveInt) -> int:
    """Calculate the number of pages for a paginated response."""
    return ceil(total / page_size)
