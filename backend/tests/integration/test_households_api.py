"""Integration tests for household and member endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.domain.enums import MEMBER_COLORS
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "test_api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_create_household_and_get_me(client: TestClient) -> None:
    res = client.post(
        "/api/v1/households",
        json={
            "household_name": "بيت أبو أحمد",
            "display_name": "أمي",
            "color": MEMBER_COLORS[0],
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert len(data["invite_code"]) == 8
    assert data["member_token"]
    assert data["household"]["name"] == "بيت أبو أحمد"
    assert data["member"]["display_name"] == "أمي"

    me_res = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {data['member_token']}"},
    )
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["member"]["id"] == data["member"]["id"]
    assert me["household"]["id"] == data["household"]["id"]
    assert len(me["members"]) == 1


def test_me_requires_valid_bearer_token(client: TestClient) -> None:
    for headers in [
        {},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer "},
        {"Authorization": "Bearer totally-invalid-token"},
    ]:
        res = client.get("/api/v1/me", headers=headers)
        assert res.status_code == 401
        body = res.json()
        assert body["error"]["code"] == "unauthorized"


def test_join_rotate_and_household_isolation(client: TestClient) -> None:
    hh1 = client.post(
        "/api/v1/households",
        json={"household_name": "بيت 1", "display_name": "أمي", "color": MEMBER_COLORS[0]},
    ).json()
    hh2 = client.post(
        "/api/v1/households",
        json={"household_name": "بيت 2", "display_name": "خالد", "color": MEMBER_COLORS[2]},
    ).json()

    join_res = client.post(
        "/api/v1/households/join",
        json={
            "invite_code": hh1["invite_code"],
            "display_name": "يونس",
            "color": MEMBER_COLORS[1],
        },
    )
    assert join_res.status_code == 200
    joined = join_res.json()
    assert joined["household"]["id"] == hh1["household"]["id"]

    # Household isolation: hh2 member only sees hh2 members
    me2 = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {hh2['member_token']}"},
    ).json()
    assert [m["display_name"] for m in me2["members"]] == ["خالد"]

    # Rotate invite code -> old code returns 404, new code works
    rot = client.post(
        "/api/v1/households/invite/rotate",
        headers={"Authorization": f"Bearer {hh1['member_token']}"},
    )
    assert rot.status_code == 200
    new_code = rot.json()["invite_code"]
    assert new_code != hh1["invite_code"]

    old_join = client.post(
        "/api/v1/households/join",
        json={"invite_code": hh1["invite_code"], "display_name": "سارة", "color": MEMBER_COLORS[3]},
    )
    assert old_join.status_code == 404

    new_join = client.post(
        "/api/v1/households/join",
        json={"invite_code": new_code, "display_name": "سارة", "color": MEMBER_COLORS[3]},
    )
    assert new_join.status_code == 200


def test_validation_errors_return_422_standard_shape(client: TestClient) -> None:
    res = client.post(
        "/api/v1/households",
        json={"household_name": "بيتنا", "display_name": "أمي", "color": "#123456"},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"

    res_empty = client.post(
        "/api/v1/households",
        json={"household_name": "بيتنا", "display_name": "   ", "color": MEMBER_COLORS[0]},
    )
    assert res_empty.status_code == 422
    assert res_empty.json()["error"]["code"] == "validation_error"


def test_join_rate_limit_returns_429(client: TestClient) -> None:
    for i in range(5):
        res = client.post(
            "/api/v1/households/join",
            json={
                "invite_code": f"WRONG{i}23",
                "display_name": "يونس",
                "color": MEMBER_COLORS[0],
            },
        )
        assert res.status_code == 404

    blocked = client.post(
        "/api/v1/households/join",
        json={
            "invite_code": "ANYCODE8",
            "display_name": "يونس",
            "color": MEMBER_COLORS[0],
        },
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"


def test_rejoin_existing_member_and_remove_member_isolation(client: TestClient) -> None:
    hh1 = client.post(
        "/api/v1/households",
        json={"household_name": "بيت 1", "display_name": "أمي", "color": MEMBER_COLORS[0]},
    ).json()
    hh2 = client.post(
        "/api/v1/households",
        json={"household_name": "بيت 2", "display_name": "خالد", "color": MEMBER_COLORS[1]},
    ).json()

    # Rejoining with the same normalized name in same household returns same member with a new token
    rejoin = client.post(
        "/api/v1/households/join",
        json={
            "invite_code": hh1["invite_code"],
            "display_name": "امي",
            "color": MEMBER_COLORS[2],
        },
    )
    assert rejoin.status_code == 200
    rejoin_data = rejoin.json()
    assert rejoin_data["member"]["id"] == hh1["member"]["id"]
    assert rejoin_data["member"]["color"] == MEMBER_COLORS[2]
    assert rejoin_data["member_token"] != hh1["member_token"]

    # Old token is invalidated; new token works
    old_me = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {hh1['member_token']}"},
    )
    assert old_me.status_code == 401
    new_me = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {rejoin_data['member_token']}"},
    )
    assert new_me.status_code == 200
    hh1["member_token"] = rejoin_data["member_token"]

    # Valid join for a second member
    joined = client.post(
        "/api/v1/households/join",
        json={
            "invite_code": hh1["invite_code"],
            "display_name": "يونس",
            "color": MEMBER_COLORS[2],
        },
    ).json()

    # Cannot remove self -> 422
    self_del = client.delete(
        f"/api/v1/households/members/{hh1['member']['id']}",
        headers={"Authorization": f"Bearer {hh1['member_token']}"},
    )
    assert self_del.status_code == 422

    # Household isolation: hh2 cannot remove hh1's member -> 404
    cross_del = client.delete(
        f"/api/v1/households/members/{joined['member']['id']}",
        headers={"Authorization": f"Bearer {hh2['member_token']}"},
    )
    assert cross_del.status_code == 404

    # hh1 removes joined member -> 204 and token is invalidated
    ok_del = client.delete(
        f"/api/v1/households/members/{joined['member']['id']}",
        headers={"Authorization": f"Bearer {hh1['member_token']}"},
    )
    assert ok_del.status_code == 204

    removed_me = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {joined['member_token']}"},
    )
    assert removed_me.status_code == 401
