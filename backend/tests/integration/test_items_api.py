"""Integration tests for items API routes, ETag, sorting, and household isolation."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.domain.enums import MEMBER_COLORS
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "test_items_api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _create_household(client: TestClient, name: str, member_name: str) -> dict[str, str]:
    res = client.post(
        "/api/v1/households",
        json={"household_name": name, "display_name": member_name, "color": MEMBER_COLORS[0]},
    )
    assert res.status_code == 201
    data = res.json()
    return {
        "token": data["member_token"],
        "member_id": data["member"]["id"],
        "household_id": data["household"]["id"],
    }


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_items_crud_sorting_etag_and_clear_bought(client: TestClient) -> None:
    hh = _create_household(client, "بيت أبو أحمد", "أمي")
    headers = _auth(hh["token"])

    # Create normal and urgent items
    r1 = client.post(
        "/api/v1/items",
        json={"name": "خبز", "quantity_text": "خبزتين", "category": "bakery"},
        headers=headers,
    )
    assert r1.status_code == 201
    bread = r1.json()
    assert bread["requested_by_member_id"] == hh["member_id"]

    r2 = client.post(
        "/api/v1/items",
        json={"name": "بيض", "category": "dairy_eggs", "urgency": "urgent"},
        headers=headers,
    )
    assert r2.status_code == 201
    eggs = r2.json()

    # Duplicate open item -> 409 with existing_item_id
    dup = client.post("/api/v1/items", json={"name": "خبز"}, headers=headers)
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "duplicate_item"
    assert dup.json()["error"]["existing_item_id"] == bread["id"]

    # List items: urgent first, then created_at ascending
    list_res = client.get("/api/v1/items", headers=headers)
    assert list_res.status_code == 200
    etag = list_res.headers["ETag"]
    items = list_res.json()["items"]
    assert [i["id"] for i in items] == [eggs["id"], bread["id"]]

    # ETag 304 Not Modified
    not_mod = client.get("/api/v1/items", headers={**headers, "If-None-Match": etag})
    assert not_mod.status_code == 304

    # PATCH item
    patch_res = client.patch(
        f"/api/v1/items/{bread['id']}",
        json={"quantity_text": "3 أرغفة", "note": "من المخبز"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["quantity_text"] == "3 أرغفة"
    assert patch_res.json()["note"] == "من المخبز"

    # Mark eggs as bought -> moves to end
    bought_res = client.post(
        f"/api/v1/items/{eggs['id']}/status",
        json={"status": "bought"},
        headers=headers,
    )
    assert bought_res.status_code == 200
    assert bought_res.json()["bought_by_member_id"] == hh["member_id"]
    assert bought_res.json()["bought_at"] is not None

    # Invalid transition bought -> cancelled returns 422
    bad_trans = client.post(
        f"/api/v1/items/{eggs['id']}/status",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert bad_trans.status_code == 422
    assert bad_trans.json()["error"]["code"] == "invalid_transition"

    # Clear bought (soft archive)
    clear_res = client.post("/api/v1/items/clear-bought", headers=headers)
    assert clear_res.status_code == 200
    assert clear_res.json()["archived_count"] == 1

    # Archived item is excluded from GET /items
    after_clear = client.get("/api/v1/items", headers=headers).json()["items"]
    assert [i["id"] for i in after_clear] == [bread["id"]]


def test_items_cross_household_isolation(client: TestClient) -> None:
    hh1 = _create_household(client, "بيت 1", "أمي")
    hh2 = _create_household(client, "بيت 2", "خالد")

    created = client.post(
        "/api/v1/items",
        json={"name": "بندورة"},
        headers=_auth(hh1["token"]),
    ).json()

    # hh2 cannot see hh1's items
    hh2_list = client.get("/api/v1/items", headers=_auth(hh2["token"])).json()["items"]
    assert hh2_list == []

    # hh2 cannot PATCH or change status of hh1's item -> 404 (not 403)
    patch_other = client.patch(
        f"/api/v1/items/{created['id']}",
        json={"name": "خيار"},
        headers=_auth(hh2["token"]),
    )
    assert patch_other.status_code == 404

    status_other = client.post(
        f"/api/v1/items/{created['id']}/status",
        json={"status": "bought"},
        headers=_auth(hh2["token"]),
    )
    assert status_other.status_code == 404


def test_items_history_and_household_isolation(client: TestClient) -> None:
    hh1 = _create_household(client, "بيت 1", "أمي")
    hh2 = _create_household(client, "بيت 2", "خالد")

    # Create two items in hh1: mark one bought, keep one open
    bought_item = client.post(
        "/api/v1/items",
        json={"name": "حليب", "category": "dairy_eggs"},
        headers=_auth(hh1["token"]),
    ).json()
    client.post(
        f"/api/v1/items/{bought_item['id']}/status",
        json={"status": "bought"},
        headers=_auth(hh1["token"]),
    )
    client.post(
        "/api/v1/items",
        json={"name": "خبز", "category": "bakery"},
        headers=_auth(hh1["token"]),
    )

    # Archive bought item -> should still appear in history
    client.post("/api/v1/items/clear-bought", headers=_auth(hh1["token"]))

    hist_res = client.get("/api/v1/items/history?limit=50", headers=_auth(hh1["token"]))
    assert hist_res.status_code == 200
    hist_items = hist_res.json()["items"]
    assert [i["id"] for i in hist_items] == [bought_item["id"]]

    # hh2 must not see hh1's history
    hh2_hist = client.get("/api/v1/items/history?limit=50", headers=_auth(hh2["token"]))
    assert hh2_hist.status_code == 200
    assert hh2_hist.json()["items"] == []
