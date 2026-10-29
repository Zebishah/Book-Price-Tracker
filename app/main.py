from fastapi import FastAPI

from app.api.books import router as books_router
from app.api.scraping import router as scraping_router


def create_app() -> FastAPI:
    # Create and configure the FastAPI application.
    app = FastAPI(
        title="Book Price Tracker API",
        description="REST API for scraped book data.",
        version="0.1.0",
    )

    app.include_router(books_router)
    app.include_router(scraping_router)

    @app.get("/", tags=["General"])
    def root() -> dict[str, str]:
        # Provide API information and links to the documentation and health check.
        return {
            "message": "Book Price Tracker API",
            "documentation": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        # Return a lightweight response for application health checks.
        return {"status": "ok"}

    return app


app = create_app()
