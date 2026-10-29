from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ScrapingJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapingJobResponse(BaseModel):
    job_id: UUID
    status: ScrapingJobStatus
    limit: int | None = None
    pages_scraped: int = Field(default=0, ge=0)
    books_scraped: int = Field(default=0, ge=0)
    created_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
