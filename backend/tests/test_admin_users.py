from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login_admin() -> str:
    response = client.post(
        "/api/auth/login",
        json={"phone_number": "+60190000000", "password": "admin1234"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def register_player() -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "overview-player",
            "phone_number": "+60124440001",
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def register_player_with_id() -> tuple[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "overview-player",
            "phone_number": "+60124440001",
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    return payload["access_token"], payload["user_id"]


def test_admin_user_overview_returns_real_counts_and_safe_fields() -> None:
    register_player()
    response = client.get(
        "/api/admin/users/overview?limit=2",
        headers=headers(login_admin()),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_users"] == 2
    assert payload["active_users"] == 2
    assert payload["player_count"] == 1
    assert payload["admin_count"] == 1
    assert len(payload["users"]) == 2
    assert any(user["username"] == "overview-player" for user in payload["users"])
    for user in payload["users"]:
        assert set(user) == {"id", "username", "role", "is_active", "created_at"}
        assert "phone_number" not in user
        assert "password_hash" not in user
        assert "auth_version" not in user


def test_player_cannot_access_admin_user_overview() -> None:
    player_token = register_player()

    response = client.get(
        "/api/admin/users/overview",
        headers=headers(player_token),
    )

    assert response.status_code == 403


def test_admin_can_search_and_open_user_detail() -> None:
    player_token, player_id = register_player_with_id()
    profile_response = client.put(
        "/api/profile",
        headers=headers(player_token),
        json={
            "skill_level": "intermediate",
            "playing_style": "attacking",
            "preferred_tension": 27,
            "frequency_per_week": 3,
            "preferred_feel": "medium",
            "preferred_gauge": "medium",
            "recent_goal": "power",
        },
    )
    assert profile_response.status_code == 200

    strings_response = client.get(
        "/api/strings",
        headers=headers(player_token),
    )
    assert strings_response.status_code == 200

    booking_response = client.post(
        "/api/bookings",
        headers=headers(player_token),
        json={
            "string_id": strings_response.json()["items"][0]["id"],
            "racket_model": "Astrox 88D Pro",
            "requested_tension": 27,
        },
    )
    assert booking_response.status_code == 200

    admin_token = login_admin()
    search_response = client.get(
        "/api/admin/users/overview",
        headers=headers(admin_token),
        params={"search": "VIEW", "limit": 20},
    )

    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert search_payload["total_users"] == 2
    assert [user["username"] for user in search_payload["users"]] == ["overview-player"]

    detail_response = client.get(
        f"/api/admin/users/{player_id}",
        headers=headers(admin_token),
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert set(detail) == {
        "id",
        "username",
        "phone_number",
        "role",
        "is_active",
        "created_at",
        "profile",
        "recent_orders",
    }
    assert detail["username"] == "overview-player"
    assert detail["phone_number"] == "+60124440001"
    assert detail["profile"]["preferred_tension"] == 27
    assert detail["profile"]["recent_goal"] == "power"
    assert len(detail["recent_orders"]) == 1
    assert (
        detail["recent_orders"][0]["order_code"]
        == booking_response.json()["order_code"]
    )
    assert "password_hash" not in detail

    player_detail_response = client.get(
        f"/api/admin/users/{player_id}",
        headers=headers(player_token),
    )
    assert player_detail_response.status_code == 403
