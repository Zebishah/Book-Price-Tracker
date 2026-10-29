from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.book import Book


def get_book_by_id(session: Session, book_id: int) -> Book | None:
    return session.get(Book, book_id)


def list_books(
    session: Session,
    *,
    page: int,
    page_size: int,
    category: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
) -> tuple[list[Book], int]:
    filters = []

    if category is not None:
        filters.append(func.lower(Book.category) == category.lower())

    if min_price is not None:
        filters.append(Book.price >= min_price)

    if max_price is not None:
        filters.append(Book.price <= max_price)

    total_statement = select(func.count()).select_from(Book).where(*filters)

    total = session.scalar(total_statement) or 0

    statement = (
        select(Book)
        .where(*filters)
        .order_by(Book.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    books = list(session.scalars(statement).all())

    return books, total
