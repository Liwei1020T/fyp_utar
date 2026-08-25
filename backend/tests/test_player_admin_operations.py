from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login_admin() -> str:
    response = client.post(
        "/api/auth/login",
        json={"phone_number": "+60190000000", "password": "admin1234"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_player_admin_operational_flow() -> None:
    register = client.post(
        "/api/auth/register",
        json={
            "username": "operations-player",
            "phone_number": "+60124440001",
            "password": "secret123",
        },
    )
    assert register.status_code == 200
    player_token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    admin_token = _login_admin()

    string_id = client.get("/api/strings", headers=_headers(player_token)).json()[
        "items"
    ][0]["id"]
    booking = client.post(
        "/api/bookings",
        headers=_headers(player_token),
        json={"string_id": string_id, "requested_tension": 27},
    ).json()
    booking_id = booking["id"]

    token_response = client.post(
        f"/api/bookings/{booking_id}/check-in-token",
        headers=_headers(player_token),
    )
    assert token_response.status_code == 200
    replaced_qr_token = token_response.json()["token"]
    replacement_response = client.post(
        f"/api/bookings/{booking_id}/check-in-token",
        headers=_headers(player_token),
    )
    assert replacement_response.status_code == 200
    qr_token = replacement_response.json()["token"]
    assert (
        client.post(
            "/api/admin/check-in/lookup",
            headers=_headers(admin_token),
            json={"token": replaced_qr_token},
        ).status_code
        == 400
    )

    lookup = client.post(
        "/api/admin/check-in/lookup",
        headers=_headers(admin_token),
        json={"token": qr_token},
    )
    assert lookup.status_code == 200
    assert lookup.json()["matched_by"] == "qr_token"

    confirm = client.post(
        "/api/admin/check-in/confirm",
        headers=_headers(admin_token),
        json={"token": qr_token},
    )
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "in_progress"
    assert (
        client.post(
            "/api/admin/check-in/confirm",
            headers=_headers(admin_token),
            json={"token": qr_token},
        ).status_code
        == 400
    )

    for status in ("ready_for_collection", "completed"):
        response = client.patch(
            f"/api/admin/bookings/{booking_id}/status",
            headers=_headers(admin_token),
            json={"status": status},
        )
        assert response.status_code == 200

    feedback = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=_headers(player_token),
        json={
            "rating": 5,
            "recommendation_relevance": 4,
            "string_satisfaction": 5,
            "tension_satisfaction": 4,
            "comfort": 4,
            "control": 5,
            "repulsion": 5,
            "would_use_again": True,
            "comment": "Great setup and service.",
        },
    )
    assert feedback.status_code == 200
    assert "durability" not in feedback.json()
    assert feedback.json()["control"] == 5

    admin_feedback = client.get(
        "/api/admin/feedback",
        headers=_headers(admin_token),
        params={"rating": 5},
    )
    assert admin_feedback.status_code == 200
    assert admin_feedback.json()["items"][0]["booking_id"] == booking_id
    export = client.get(
        "/api/admin/feedback/export",
        headers=_headers(admin_token),
    )
    assert export.status_code == 200
    assert "recommendation_relevance" in export.text

    notification = client.post(
        "/api/admin/notifications",
        headers=_headers(admin_token),
        json={
            "user_id": user_id,
            "category": "system",
            "title": "Counter update",
            "body": "Your racket is ready.",
            "route": f"/player/bookings/{booking_id}",
        },
    )
    assert notification.status_code == 200
    assert notification.json()["status"] == "failed"
    assert notification.json()["provider_message"] == "No active device token"
    feed = client.get("/api/notifications", headers=_headers(player_token))
    assert any(item["title"] == "Counter update" for item in feed.json())

    privacy = client.put(
        "/api/profile/privacy",
        headers=_headers(player_token),
        json={
            "analytics_consent": False,
            "personalization_consent": True,
            "marketing_consent": False,
        },
    )
    assert privacy.status_code == 200
    assert privacy.json()["analytics_consent"] is False

    password = client.post(
        "/api/auth/change-password",
        headers=_headers(player_token),
        json={"current_password": "secret123", "new_password": "changed123"},
    )
    assert password.status_code == 200
    assert client.get("/api/auth/me", headers=_headers(player_token)).status_code == 401
    login = client.post(
        "/api/auth/login",
        json={"phone_number": "+60124440001", "password": "changed123"},
    )
    assert login.status_code == 200
    deletion = client.post(
        "/api/auth/delete-account-request",
        headers=_headers(login.json()["access_token"]),
        json={"reason": "No longer needed"},
    )
    assert deletion.status_code == 200
    assert deletion.json()["status"] == "pending"
