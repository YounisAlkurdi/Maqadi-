"""Integration tests for /api/v1/paste/* endpoints."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.domain.enums import MEMBER_COLORS
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    db_path = tmp_path / "test_paste.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("TOKEN_PEPPER", "test-pepper")
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c
    get_settings.cache_clear()


def _create_household(client: TestClient, name: str = "بيتنا", member: str = "أم يوسف") -> str:
    res = client.post(
        "/api/v1/households",
        json={"household_name": name, "display_name": member, "color": MEMBER_COLORS[0]},
    )
    assert res.status_code == 201
    return res.json()["member_token"]


def test_paste_preview_requires_auth(client: TestClient) -> None:
    res = client.post("/api/v1/paste/preview", json={"text": "جيب لبن"})
    assert res.status_code == 401


def test_paste_preview_rules_engine(client: TestClient) -> None:
    token = _create_household(client)
    res = client.post(
        "/api/v1/paste/preview",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "السلام عليكم\nجيب لبن وخبز ضروري"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["engine"] == "rules"
    assert len(data["items"]) >= 2
    assert len(data["ignored"]) == 1


def test_paste_preview_too_long_returns_422(client: TestClient) -> None:
    token = _create_household(client)
    res = client.post(
        "/api/v1/paste/preview",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "أ" * 6001},
    )
    assert res.status_code == 422


def test_paste_confirm_persists_items_and_household_isolation(client: TestClient) -> None:
    token_a = _create_household(client, name="بيت أ", member="أحمد")
    token_b = _create_household(client, name="بيت ب", member="سارة")

    confirm_res = client.post(
        "/api/v1/paste/confirm",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "items": [
                {
                    "name": "لبن",
                    "quantity_text": "2 لتر",
                    "category": "dairy_eggs",
                    "urgency": "normal",
                },
                {"name": "خبز", "category": "bakery", "urgency": "urgent"},
            ]
        },
    )
    assert confirm_res.status_code == 200
    assert len(confirm_res.json()["items"]) == 2

    # Household A sees the 2 items
    list_a = client.get("/api/v1/items", headers={"Authorization": f"Bearer {token_a}"})
    assert list_a.status_code == 200
    assert len(list_a.json()["items"]) == 2

    # Household B sees 0 items (household isolation)
    list_b = client.get("/api/v1/items", headers={"Authorization": f"Bearer {token_b}"})
    assert list_b.status_code == 200
    assert len(list_b.json()["items"]) == 0
