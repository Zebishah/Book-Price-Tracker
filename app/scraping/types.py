from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ScrapedBook:
    title: str
    price: Decimal
    rating: int
    availability: str
    category: str
    product_url: str
