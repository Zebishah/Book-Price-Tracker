import httpx
import pytest

from app.scraping.client import ScrapingClient, ScrapingError

TEST_URL = "https://books.toscrape.com/"


def test_fetch_returns_html() -> None:
    # Verify fetch returns html.
    def handler(request: httpx.Request) -> httpx.Response:
        # Return a mocked HTTP response for the client test.
        return httpx.Response(
            200,
            text="<html><body>Books</body></html>",
        )

    with ScrapingClient() as client:
        client._client.close()
        client._client = httpx.Client(
            transport=httpx.MockTransport(handler),
        )

        result = client.fetch(TEST_URL)

    assert result == "<html><body>Books</body></html>"


def test_fetch_rejects_non_retryable_http_error() -> None:
    # Verify fetch rejects non retryable http error.
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        # Return a mocked HTTP response for the client test.
        nonlocal attempts
        attempts += 1
        return httpx.Response(404)

    with ScrapingClient() as client:
        client._client.close()
        client._client = httpx.Client(
            transport=httpx.MockTransport(handler),
        )

        with pytest.raises(ScrapingError):
            client.fetch(TEST_URL)

    assert attempts == 1
