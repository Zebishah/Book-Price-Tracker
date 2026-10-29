from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.schemas.scraping import ScrapingJobStatus
from app.services import scraping_jobs
from app.services.scraper import ScrapingResult
from app.services.scraping_jobs import (
    ScrapingAlreadyRunningError,
    ScrapingJobManager,
)


def test_job_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = ScrapingJobManager()

    fake_scrape = Mock(
        return_value=ScrapingResult(
            pages_scraped=1,
            books_scraped=5,
        )
    )

    monkeypatch.setattr(scraping_jobs, "scrape_books", fake_scrape)

    job = manager.create_job(limit=5)

    assert job.status == ScrapingJobStatus.PENDING

    manager.run_job(job.job_id)

    completed = manager.get_job(job.job_id)

    assert completed is not None
    assert completed.status == ScrapingJobStatus.COMPLETED
    assert completed.books_scraped == 5
    assert completed.pages_scraped == 1
    assert completed.completed_at is not None

    assert fake_scrape.call_args.kwargs["max_books"] == 5


def test_rejects_concurrent_jobs() -> None:
    manager = ScrapingJobManager()
    manager.create_job(limit=10)

    with pytest.raises(ScrapingAlreadyRunningError):
        manager.create_job(limit=20)


def test_unknown_job_returns_none() -> None:
    manager = ScrapingJobManager()

    assert manager.get_job(uuid4()) is None
