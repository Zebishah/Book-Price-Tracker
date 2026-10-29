import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.book import Book
from app.scraping.client import BASE_URL, ScrapingClient
from app.scraping.parser import parse_book, parse_listing
from app.scraping.types import ScrapedBook

REQUEST_DELAY_SECONDS = 0.2
MAX_CATALOGUE_PAGES = 100

SessionFactory = Callable[[], Session]


class ScrapingLimitError(RuntimeError):
    """Raised when pagination exceeds the configured safety limit."""


@dataclass(frozen=True, slots=True)
class ScrapingResult:
    pages_scraped: int
    books_scraped: int


def save_books(session: Session, books: list[ScrapedBook]) -> None:
    """Insert books or update existing records by product URL."""
    if not books:
        return

    rows = [
        {
            "title": book.title,
            "price": book.price,
            "rating": book.rating,
            "availability": book.availability,
            "category": book.category,
            "product_url": book.product_url,
        }
        for book in books
    ]

    statement = insert(Book).values(rows)

    statement = statement.on_conflict_do_update(
        index_elements=[Book.product_url],
        set_={
            "title": statement.excluded.title,
            "price": statement.excluded.price,
            "rating": statement.excluded.rating,
            "availability": statement.excluded.availability,
            "category": statement.excluded.category,
            "scraped_at": func.now(),
        },
    )

    session.execute(statement)


def scrape_books(
    *,
    client: ScrapingClient,
    session_factory: SessionFactory = SessionLocal,
    delay_seconds: float = REQUEST_DELAY_SECONDS,
    max_pages: int = MAX_CATALOGUE_PAGES,
    start_url: str = BASE_URL,
    max_books: int | None = None,
) -> ScrapingResult:
    """Scrape catalogue pages and persist book records."""

    if delay_seconds < 0:
        raise ValueError("Request delay must not be negative")

    if max_pages < 1:
        raise ValueError("Maximum pages must be at least one")
    if max_books is not None and max_books < 1:
        raise ValueError("Maximum books must be at least one")
    # Validate the starting catalogue URL
    parsed_url = urlparse(start_url)

    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "books.toscrape.com"
        or not (
            parsed_url.path == "/"
            or (
                parsed_url.path.startswith("/catalogue/page-")
                and parsed_url.path.endswith(".html")
            )
        )
    ):
        raise ValueError("Invalid catalogue start URL")

    # Initialize scraping state
    current_url: str | None = start_url
    visited_pages: set[str] = set()

    pages_scraped = 0
    books_scraped = 0

    # Keep your existing fetch_page() and while-loop code below.

    def fetch_page(url: str) -> str:
        time.sleep(delay_seconds)
        return client.fetch(url)

    while current_url is not None:
        if current_url in visited_pages:
            raise ScrapingLimitError(f"Pagination cycle detected at {current_url}")

        visited_pages.add(current_url)

        listing_html = fetch_page(current_url)
        product_urls, next_url = parse_listing(
            listing_html,
            current_url,
        )

        books: list[ScrapedBook] = []

        remaining = (
            max_books - books_scraped if max_books is not None else len(product_urls)
        )

        for product_url in product_urls[:remaining]:
            product_html = fetch_page(product_url)
            book = parse_book(product_html, product_url)
            books.append(book)

        # Commit one complete catalogue page at a time.
        with session_factory() as session, session.begin():
            save_books(session, books)

        pages_scraped += 1
        books_scraped += len(books)

        if max_books is not None and books_scraped >= max_books:
            break

        if pages_scraped >= max_pages:
            break

        current_url = next_url

    return ScrapingResult(
        pages_scraped=pages_scraped,
        books_scraped=books_scraped,
    )
