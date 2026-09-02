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
