from decimal import Decimal

import pytest

from app.scraping.parser import (
    ParsingError,
    parse_book,
    parse_listing,
)

BASE_URL = "https://books.toscrape.com/"


def test_parse_listing_extracts_product_urls_and_next_page() -> None:
    html = """
    <article class="product_pod">
        <h3><a href="a-light-in-the-attic_1000/index.html">Book</a></h3>
    </article>
    <li class="next"><a href="page-2.html">Next</a></li>
    """

    urls, next_url = parse_listing(
        html,
        f"{BASE_URL}catalogue/page-1.html",
    )

    assert urls == [f"{BASE_URL}catalogue/a-light-in-the-attic_1000/index.html"]
    assert next_url == f"{BASE_URL}catalogue/page-2.html"


def test_parse_book_extracts_required_fields() -> None:
    html = """
    <ul class="breadcrumb">
        <li>Home</li>
        <li>Books</li>
        <li><a>Poetry</a></li>
        <li>A Light in the Attic</li>
    </ul>

    <div class="product_main">
        <h1>A Light in the Attic</h1>
        <p class="price_color">£51.77</p>
        <p class="availability">In stock (22 available)</p>
        <p class="star-rating Three"></p>
    </div>
    """

    book = parse_book(
        html,
        f"{BASE_URL}catalogue/a-light-in-the-attic_1000/index.html",
    )

    assert book.title == "A Light in the Attic"
    assert book.price == Decimal("51.77")
    assert book.rating == 3
    assert book.availability == "In stock (22 available)"
    assert book.category == "Poetry"


def test_parse_book_rejects_missing_required_data() -> None:
    with pytest.raises(ParsingError):
        parse_book(
            "<html><body></body></html>",
            f"{BASE_URL}catalogue/example/index.html",
        )


def test_parse_listing_rejects_external_urls() -> None:
    html = """
    <article class="product_pod">
        <h3><a href="https://example.com/book">Book</a></h3>
    </article>
    """

    with pytest.raises(ParsingError):
        parse_listing(html, f"{BASE_URL}catalogue/page-1.html")
