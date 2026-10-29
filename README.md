
# Book Price Tracker API

A REST API built with FastAPI that scrapes book information from [Books to Scrape](https://books.toscrape.com/), stores it in PostgreSQL, and exposes endpoints for retrieving and filtering books.

## Tech Stack

- **Python 3.12**
- **FastAPI** — REST API
- **HTTPX + BeautifulSoup** — Web scraping
- **SQLAlchemy 2.x** — Database ORM
- **PostgreSQL** — Data storage
- **Alembic** — Database migrations
- **Pydantic** — Request validation and response serialization
- **Docker Compose** — Containerized application and database
- **Pytest + Ruff** — Testing, linting, and formatting
- **uv** — Dependency management

## Features

- Scrape book titles, prices, ratings, availability, and categories.
- Follow catalogue pagination.
- Insert new books and update existing records without duplicates.
- Retrieve books using paginated REST endpoints.
- Filter by category and price range.
- Scrape a configurable number of books.
- Trigger scraping through background tasks and check job status.
- Apply database migrations automatically in Docker.

## Quick Start with Docker

### Requirements

Docker Engine with Docker Compose support.

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd Book-Price-Tracker
```

### 2. Start the application

```bash
docker compose up --build -d
```

Docker Compose starts PostgreSQL and FastAPI. Alembic migrations run automatically before the API starts.

### 3. Open the API documentation

Swagger UI:

http://localhost:8000/docs

Health check:

http://localhost:8000/health

### 4. Scrape books

To scrape the first 20 books:

```bash
curl -X POST "http://localhost:8000/scrape?limit=20"
```

The endpoint returns HTTP 202 with a job ID.

Check the job status:

```bash
curl "http://localhost:8000/scrape/jobs/JOB_ID"
```

Replace `JOB_ID` with the returned UUID.

To scrape the entire catalogue:

```bash
curl -X POST "http://localhost:8000/scrape"
```

A full scrape may take several minutes.

### 5. Retrieve books

```bash
# List books
curl "http://localhost:8000/books"

# Pagination
curl "http://localhost:8000/books?page=2&page_size=10"

# Retrieve one book
curl "http://localhost:8000/books/1"

# Category filter
curl "http://localhost:8000/books?category=Poetry"

# Price range
curl "http://localhost:8000/books?min_price=20&max_price=40"

# Combined filters
curl "http://localhost:8000/books?category=Fiction&min_price=10&max_price=40"
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Application health |
| GET | `/books` | Paginated books with optional filters |
| GET | `/books/{book_id}` | Retrieve a specific book |
| POST | `/scrape` | Start a scraping job |
| GET | `/scrape/jobs/{job_id}` | Retrieve scraping job status |

### Scraping Parameters

`POST /scrape` accepts an optional `limit` query parameter between 1 and 1000.

If omitted, the scraper processes the available catalogue.

### Book Pagination Parameters

- `page`: Page number, starting at 1.
- `page_size`: Number of records per page, between 1 and 100.
- `category`: Case-insensitive category filter.
- `min_price`: Minimum price, inclusive.
- `max_price`: Maximum price, inclusive.

Prices are stored in GBP.

## Local Development

Install [uv](https://docs.astral.sh/uv/) and Python 3.12 or newer.

Install dependencies:

```bash
uv sync
```

Create a `.env` file based on `.env.example` and configure a PostgreSQL connection.

Run migrations:

```bash
uv run alembic upgrade head
```

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

## Testing

Run all automated tests:

```bash
uv run pytest -v
```

Run linting and formatting checks:

```bash
uv run ruff check .
uv run ruff format --check .
```

## Database

SQLAlchemy defines the `books` table and Alembic manages schema migrations.

The `product_url` column has a unique constraint. Repeated scraping uses PostgreSQL upserts to update existing records rather than create duplicates.

The `scraped_at` timestamp records when a book was most recently saved.

Docker Compose uses its own PostgreSQL instance with persistent volume storage. It does not require a Neon database or access to the developer's personal database credentials.

## Design Notes

- HTTP fetching, HTML parsing, database access, and API handlers are separated into focused modules.
- Scraping processes book detail pages sequentially.
- Database writes use page-level transactions.
- HTTP requests have configured timeouts and retries.
- Scraping jobs are tracked in memory and only one can run at a time per application process.
- Background jobs are not persisted across process restarts.
- The Docker setup runs one API worker because job state is in memory.

## Security and Deployment

The Docker Compose configuration is intended for local development and assignment evaluation.

The API is bound to localhost by default. Scraping endpoints have no authentication and should not be exposed publicly without access controls.

Production deployment would require persistent background job storage, appropriate authentication, managed credentials, and operational monitoring.

## Stopping the Application

```bash
docker compose down
```

This preserves the PostgreSQL data volume.

Running `docker compose down -v` also removes the database volume and its stored data.
