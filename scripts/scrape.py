import argparse
import logging
import time

from app.scraping.client import ScrapingClient
from app.services.scraper import scrape_books

logger = logging.getLogger(__name__)


def main() -> int:
    # Parse CLI arguments and run scraping independently of the API.
    parser = argparse.ArgumentParser(
        description="Scrape books and save them to PostgreSQL.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of books to scrape (default: all).",
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be a positive integer")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    started = time.monotonic()

    try:
        with ScrapingClient() as client:
            result = scrape_books(
                client=client,
                max_books=args.limit,
            )
    except Exception:
        logger.exception("Scraping failed")
        return 1

    elapsed = time.monotonic() - started

    print("\nScraping completed successfully.")
    print(f"Pages scraped: {result.pages_scraped}")
    print(f"Books processed: {result.books_scraped}")
    print(f"Duration: {elapsed:.2f} seconds")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
