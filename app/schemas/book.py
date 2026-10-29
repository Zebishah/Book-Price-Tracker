from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: Decimal
    rating: int
    availability: str
    category: str
    product_url: str
    scraped_at: datetime


class PaginatedBooksResponse(BaseModel):
    items: list[BookResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
