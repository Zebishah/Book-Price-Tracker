from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
    status,
)

from app.schemas.scraping import ScrapingJobResponse
from app.services.scraping_jobs import (
    ScrapingAlreadyRunningError,
    scraping_job_manager,
)

router = APIRouter(tags=["Scraping"])


@router.post(
    "/scrape",
    response_model=ScrapingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_scraping(
    background_tasks: BackgroundTasks,
    limit: Annotated[
        int | None,
        Query(ge=1, le=1000),
    ] = None,
) -> ScrapingJobResponse:
    try:
        job = scraping_job_manager.create_job(limit)
    except ScrapingAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    background_tasks.add_task(
        scraping_job_manager.run_job,
        job.job_id,
    )

    return job


@router.get(
    "/scrape/jobs/{job_id}",
    response_model=ScrapingJobResponse,
)
def get_scraping_job(job_id: UUID) -> ScrapingJobResponse:
    job = scraping_job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found",
        )

    return job
