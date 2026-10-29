import logging
from datetime import UTC, datetime
from threading import Lock
from uuid import UUID, uuid4

from app.schemas.scraping import (
    ScrapingJobResponse,
    ScrapingJobStatus,
)
from app.scraping.client import ScrapingClient
from app.services.scraper import scrape_books

logger = logging.getLogger(__name__)


class ScrapingAlreadyRunningError(Exception):
    """Raised when another scraping job is already active."""


class ScrapingJobManager:
    def __init__(self) -> None:
        # Initialize in-memory job tracking and its lock.
        self._lock = Lock()
        self._jobs: dict[UUID, ScrapingJobResponse] = {}
        self._active_job_id: UUID | None = None

    def create_job(self, limit: int | None) -> ScrapingJobResponse:
        # Register a new scraping job if no job is active.
        with self._lock:
            if self._active_job_id is not None:
                raise ScrapingAlreadyRunningError("A scraping job is already active")

            job = ScrapingJobResponse(
                job_id=uuid4(),
                status=ScrapingJobStatus.PENDING,
                limit=limit,
                created_at=datetime.now(UTC),
            )

            self._jobs[job.job_id] = job
            self._active_job_id = job.job_id
            return job.model_copy(deep=True)

    def get_job(self, job_id: UUID) -> ScrapingJobResponse | None:
        # Look up a scraping job by its unique ID.
        with self._lock:
            job = self._jobs.get(job_id)
            return job.model_copy(deep=True) if job else None

    def run_job(self, job_id: UUID) -> None:
        # Execute a scraping job and record its final status.
        with self._lock:
            job = self._jobs[job_id]
            job.status = ScrapingJobStatus.RUNNING
            limit = job.limit

        try:
            with ScrapingClient() as client:
                result = scrape_books(
                    client=client,
                    max_books=limit,
                )

        except Exception:
            logger.exception("Scraping job %s failed", job_id)

            with self._lock:
                job.status = ScrapingJobStatus.FAILED
                job.error = "Scraping failed. Check server logs."

        else:
            with self._lock:
                job.status = ScrapingJobStatus.COMPLETED
                job.pages_scraped = result.pages_scraped
                job.books_scraped = result.books_scraped

        finally:
            with self._lock:
                job.completed_at = datetime.now(UTC)
                self._active_job_id = None


scraping_job_manager = ScrapingJobManager()
