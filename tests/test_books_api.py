from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.book import Book


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                Book(
                    title="Python Basics",
                    price=Decimal("20.00"),
                    rating=4,
                    availability="In stock",
                    category="Programming",
                    product_url="https://books.toscrape.com/catalogue/python_1/index.html",
                ),
                Book(
                    title="Advanced Python",
                    price=Decimal("50.00"),
                    rating=5,
                    availability="In stock",
                    category="Programming",
                    product_url="https://books.toscrape.com/catalogue/python_2/index.html",
                ),
                Book(
                    title="History Book",
                    price=Decimal("15.00"),
                    rating=3,
                    availability="In stock",
                    category="History",
                    product_url="https://books.toscrape.com/catalogue/history_3/index.html",
                ),
            ]
        )
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_list_books_with_pagination(client: TestClient) -> None:
    response = client.get("/books?page=1&page_size=2")

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["total_pages"] == 2


def test_get_book_by_id(client: TestClient) -> None:
    response = client.get("/books/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Python Basics"


def test_filter_by_category(client: TestClient) -> None:
    response = client.get("/books?category=programming")

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_filter_by_price_range(client: TestClient) -> None:
    response = client.get("/books?min_price=20&max_price=50")

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_combined_filters(client: TestClient) -> None:
    response = client.get("/books?category=Programming&min_price=40")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Advanced Python"


def test_missing_book_returns_404(client: TestClient) -> None:
    response = client.get("/books/999")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "query",
    [
        "page=0",
        "page_size=0",
        "page_size=101",
        "min_price=-1",
        "min_price=50&max_price=10",
    ],
)
def test_invalid_filters_return_422(
    client: TestClient,
    query: str,
) -> None:
    response = client.get(f"/books?{query}")

    assert response.status_code == 422
