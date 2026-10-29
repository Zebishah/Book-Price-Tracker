from fastapi import FastAPI

from app.api.books import router as books_router
from app.api.scraping import router as scraping_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Book Price Tracker API",
        description="REST API for scraped book data.",
        version="0.1.0",
    )

    app.include_router(books_router)
    app.include_router(scraping_router)

    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
