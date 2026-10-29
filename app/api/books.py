from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.book import BookResponse, PaginatedBooksResponse
from app.services.books import get_book_by_id, list_books

router = APIRouter(prefix="/books", tags=["Books"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=PaginatedBooksResponse)
def get_books(
    session: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: Annotated[
        str | None,
        Query(min_length=1, max_length=150),
    ] = None,
    min_price: Annotated[
        Decimal | None,
        Query(ge=0, allow_inf_nan=False),
    ] = None,
    max_price: Annotated[
        Decimal | None,
        Query(ge=0, allow_inf_nan=False),
    ] = None,
) -> PaginatedBooksResponse:
    # Return a paginated list of books with optional filters.
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=422,
            detail="min_price must be less than or equal to max_price",
        )

    books, total = list_books(
        session,
        page=page,
        page_size=page_size,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )

    return PaginatedBooksResponse(
        items=[BookResponse.model_validate(book) for book in books],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int,
    session: DbSession,
) -> BookResponse:
    # Fetch one book by ID or return a 404 response.
    if book_id < 1:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    book = get_book_by_id(session, book_id)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    return BookResponse.model_validate(book)
