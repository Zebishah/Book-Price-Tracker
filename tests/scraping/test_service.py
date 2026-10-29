from unittest.mock import MagicMock, Mock

import pytest

from app.scraping.client import BASE_URL, ScrapingClient
from app.services.scraper import (
    ScrapingLimitError,
    scrape_books,
)

PRODUCT_URL = f"{BASE_URL}catalogue/a-light-in-the-attic_1000/index.html"

LISTING_HTML = """
<article class="product_pod">
    <h3>
        <a href="catalogue/a-light-in-the-attic_1000/index.html">
            Book
        </a>
    </h3>
</article>
"""

PRODUCT_HTML = """
<ul class="breadcrumb">
    <li>Home</li>
    <li>Books</li>
    <li>Poetry</li>
    <li>A Light in the Attic</li>
</ul>

<div class="product_main">
    <h1>A Light in the Attic</h1>
    <p class="price_color">£51.77</p>
    <p class="availability">In stock (22 available)</p>
    <p class="star-rating Three"></p>
</div>
"""


def test_scrape_books_detects_pagination_cycle() -> None:
    listing_html = (
        LISTING_HTML
        + """
    <li class="next">
        <a href="catalogue/page-2.html">Next</a>
    </li>
    """
    )

    repeating_listing = (
        LISTING_HTML
        + """
    <li class="next">
        <a href="page-2.html">Next</a>
    </li>
    """
    )

    client = Mock(spec=ScrapingClient)
    client.fetch.side_effect = [
        listing_html,
        PRODUCT_HTML,
        repeating_listing,
        PRODUCT_HTML,
    ]

    session = MagicMock()
    session.__enter__.return_value = session
    session_factory = Mock(return_value=session)

    with pytest.raises(ScrapingLimitError, match="Pagination cycle"):
        scrape_books(
            client=client,
            session_factory=session_factory,
            delay_seconds=0,
        )

    assert client.fetch.call_count == 4
    assert session.execute.call_count == 2


def test_scrape_books_respects_exact_book_limit() -> None:
    listing_with_two_books = (
        LISTING_HTML
        + """
    <article class="product_pod">
        <h3>
            <a href="catalogue/another-book_999/index.html">
                Another book
            </a>
        </h3>
    </article>
    """
    )

    client = Mock(spec=ScrapingClient)
    client.fetch.side_effect = [
        listing_with_two_books,
        PRODUCT_HTML,
    ]

    session = MagicMock()
    session.__enter__.return_value = session
    session_factory = Mock(return_value=session)

    result = scrape_books(
        client=client,
        session_factory=session_factory,
        max_books=1,
        delay_seconds=0,
    )

    assert result.pages_scraped == 1
    assert result.books_scraped == 1

    # One listing request and only one product request.
    assert client.fetch.call_count == 2

    # One database upsert operation.
    assert session.execute.call_count == 1


def test_scrape_books_persists_complete_page() -> None:
    client = Mock(spec=ScrapingClient)
    client.fetch.side_effect = [LISTING_HTML, PRODUCT_HTML]

    session = MagicMock()
    session.__enter__.return_value = session

    session_factory = Mock(return_value=session)

    result = scrape_books(
        client=client,
        session_factory=session_factory,
        delay_seconds=0,
    )

    assert result.pages_scraped == 1
    assert result.books_scraped == 1

    client.fetch.assert_any_call(BASE_URL)
    client.fetch.assert_any_call(PRODUCT_URL)

    assert session.execute.call_count == 1
    transaction = session.begin.return_value

    transaction.__enter__.assert_called_once()
    transaction.__exit__.assert_called_once()
    session.__exit__.assert_called_once()
    session.begin.assert_called_once()
    session_factory.assert_called_once()


def test_scrape_books_does_not_persist_incomplete_page() -> None:
    client = Mock(spec=ScrapingClient)
    client.fetch.side_effect = [
        LISTING_HTML,
        "<html></html>",
    ]

    session_factory = Mock()

    with pytest.raises(ValueError):
        scrape_books(
            client=client,
            session_factory=session_factory,
            delay_seconds=0,
        )

    session_factory.assert_not_called()


def test_scrape_books_rejects_invalid_configuration() -> None:
    client = Mock(spec=ScrapingClient)

    with pytest.raises(ValueError):
        scrape_books(client=client, delay_seconds=-1)

    with pytest.raises(ValueError):
        scrape_books(client=client, max_pages=0)


def test_scrape_books_respects_page_limit() -> None:
    listing_with_next = (
        LISTING_HTML
        + """
    <li class="next">
        <a href="catalogue/page-2.html">Next</a>
    </li>
    """
    )

    client = Mock(spec=ScrapingClient)
    client.fetch.side_effect = [
        listing_with_next,
        PRODUCT_HTML,
    ]

    session = MagicMock()
    session.__enter__.return_value = session
    session_factory = Mock(return_value=session)

    result = scrape_books(
        client=client,
        session_factory=session_factory,
        delay_seconds=0,
        max_pages=1,
    )

    assert result.pages_scraped == 1
    assert result.books_scraped == 1
    assert session.execute.call_count == 1
    assert client.fetch.call_count == 2
