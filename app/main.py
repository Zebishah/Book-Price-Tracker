from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Book Price Tracker API",
        description="REST API for scraped book data.",
        version="0.1.0",
    )

    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
