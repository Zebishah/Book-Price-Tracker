from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from app.scraping.types import ScrapedBook

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


class ParsingError(ValueError):
    """Raised when required book data is missing or invalid."""


def _required_text(soup: BeautifulSoup, selector: str) -> str:
    # Extract required text from an HTML element.
    element = soup.select_one(selector)

    if element is None:
        raise ParsingError(f"Missing required element: {selector}")

    value = element.get_text(" ", strip=True)

    if not value:
        raise ParsingError(f"Empty required element: {selector}")

    return value


def _absolute_url(base_url: str, href: str) -> str:
    # Resolve and validate a link against the catalogue URL.
    url = urljoin(base_url, href)
    parsed = urlparse(url)

    if (
        parsed.scheme != "https"
        or parsed.hostname != "books.toscrape.com"
        or not parsed.path.startswith("/catalogue/")
    ):
        raise ParsingError(f"Unexpected URL: {url}")

    return url


def parse_listing(html: str, page_url: str) -> tuple[list[str], str | None]:
    # Extract book links and pagination from a catalogue page.
    soup = BeautifulSoup(html, "html.parser")
    product_urls: list[str] = []

    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a")

        if not isinstance(link, Tag):
            raise ParsingError("Book listing is missing its product link")

        href = link.get("href")

        if not isinstance(href, str) or not href:
            raise ParsingError("Book listing contains an invalid URL")

        product_urls.append(_absolute_url(page_url, href))

    if not product_urls:
        raise ParsingError("No books found on catalogue page")

    next_link = soup.select_one("li.next a")
    next_url = None

    if isinstance(next_link, Tag):
        href = next_link.get("href")

        if not isinstance(href, str) or not href:
            raise ParsingError("Invalid next-page link")

        next_url = _absolute_url(page_url, href)

    return product_urls, next_url


def parse_book(html: str, product_url: str) -> ScrapedBook:
    # Parse and validate a book's detail page.
    soup = BeautifulSoup(html, "html.parser")

    title = _required_text(soup, ".product_main h1")
    price_text = _required_text(soup, ".product_main .price_color")
    availability = _required_text(soup, ".product_main .availability")

    try:
        price = Decimal(price_text.removeprefix("£").strip())
    except InvalidOperation as exc:
        raise ParsingError(f"Invalid book price: {price_text}") from exc

    if not price.is_finite() or price < 0:
        raise ParsingError(f"Invalid book price: {price_text}")

    rating_element = soup.select_one(".product_main .star-rating")

    if not isinstance(rating_element, Tag):
        raise ParsingError("Book rating is missing")

    rating = next(
        (
            value
            for name, value in RATING_MAP.items()
            if name in rating_element.get("class", [])
        ),
        None,
    )

    if rating is None:
        raise ParsingError("Unknown book rating")

    breadcrumbs = soup.select("ul.breadcrumb li")

    if len(breadcrumbs) < 4:
        raise ParsingError("Book category is missing")

    category = breadcrumbs[-2].get_text(" ", strip=True)

    if not category:
        raise ParsingError("Book category is empty")

    return ScrapedBook(
        title=title,
        price=price,
        rating=rating,
        availability=availability,
        category=category,
        product_url=_absolute_url(product_url, product_url),
    )
