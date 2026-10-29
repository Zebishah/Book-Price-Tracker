from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api import scraping as scraping_api
from app.main import app
from app.services.scraping_jobs import ScrapingJobManager


def test_scrape_endpoint_accepts_limited_job(monkeypatch) -> None:
    manager = ScrapingJobManager()
    runner = Mock()

    monkeypatch.setattr(
        scraping_api,
        "scraping_job_manager",
        manager,
    )
    monkeypatch.setattr(manager, "run_job", runner)

    with TestClient(app) as client:
        response = client.post("/scrape?limit=5")

        assert response.status_code == 202

        data = response.json()

        assert data["status"] == "pending"
        assert data["limit"] == 5

        job_response = client.get(f"/scrape/jobs/{data['job_id']}")

        assert job_response.status_code == 200
        assert job_response.json()["job_id"] == data["job_id"]

    runner.assert_called_once()


def test_scrape_endpoint_rejects_invalid_limit() -> None:
    with TestClient(app) as client:
        assert client.post("/scrape?limit=0").status_code == 422
        assert client.post("/scrape?limit=1001").status_code == 422


def test_unknown_scraping_job_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/scrape/jobs/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
