"""Integration tests for healthz and static frontend serving."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_healthz_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_rtl_arabic_frontend() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert 'lang="ar"' in response.text
    assert 'dir="rtl"' in response.text
    assert "طلبات البيت" in response.text
