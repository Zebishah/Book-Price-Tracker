import logging
import time
from typing import Self

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"
REQUEST_TIMEOUT = 15.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ScrapingError(Exception):
    """Raised when a page cannot be retrieved."""


class ScrapingClient:
    def __init__(self) -> None:
        # Initialize the HTTP client and request settings.
        self._client = httpx.Client(
            timeout=httpx.Timeout(
                connect=5.0,
                read=10.0,
                write=10.0,
                pool=5.0,
            ),
            follow_redirects=True,
            headers={
                "User-Agent": "BookPriceTracker/1.0 (educational project)",
            },
        )

    def fetch(self, url: str) -> str:
        # Download a page with retry and error handling.
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.get(url)
                logger.info(
                    "Fetching URL (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    url,
                )
                if (
                    response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < MAX_RETRIES - 1
                ):
                    time.sleep(RETRY_DELAY * (2**attempt))
                    continue

                response.raise_for_status()
                return response.text

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                logger.warning(
                    "HTTP request failed: %s | %s",
                    url,
                    type(exc).__name__,
                )
                retryable = isinstance(exc, httpx.RequestError) or (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code in RETRYABLE_STATUS_CODES
                )

                if retryable and attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2**attempt))
                    continue

                raise ScrapingError(f"Failed to fetch {url}") from exc

        raise ScrapingError(f"Failed to fetch {url}")

    def close(self) -> None:
        # Close the underlying HTTP client.
        self._client.close()

    def __enter__(self) -> Self:
        # Return the client when entering a context manager.
        return self

    def __exit__(self, *args: object) -> None:
        # Release HTTP resources when leaving a context manager.
        self.close()
