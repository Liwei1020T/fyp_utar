from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_customer(
    *,
    username: str,
    phone_number: str,
) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "phone_number": phone_number,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def login_admin() -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60190000000",
            "password": "admin1234",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def first_string_id(token: str) -> str:
    response = client.get("/api/strings", headers=headers(token))
    assert response.status_code == 200
    return response.json()["items"][0]["id"]


def create_racket(token: str) -> dict[str, object]:
    response = client.post(
        "/api/rackets",
        headers=headers(token),
        json={
            "nickname": "Match Day 88D",
            "brand": "Yonex",
            "model": "Astrox 88D Pro",
            "weight_class": "3U",
            "balance_point": "Head heavy",
            "grip_size": "G5",
            "preferred_use": "Attack-heavy doubles",
            "notes": "Keep the string bed crisp.",
        },
    )
    assert response.status_code == 200
    return response.json()


def create_booking(token: str, racket_id: str) -> dict[str, object]:
    response = client.post(
        "/api/bookings",
        headers=headers(token),
        json={
            "string_id": first_string_id(token),
            "racket_id": racket_id,
            "racket_brand": "Spoofed brand",
            "racket_model": "Spoofed model",
            "requested_tension": 27,
        },
    )
    assert response.status_code == 200
    return response.json()


def complete_booking(admin_token: str, booking_id: str) -> None:
    for status in ("in_progress", "ready_for_collection", "completed"):
        response = client.patch(
            f"/api/admin/bookings/{booking_id}/status",
            headers=headers(admin_token),
            json={"status": status},
        )
        assert response.status_code == 200


def test_racket_crud_ownership_and_booking_snapshot() -> None:
    owner_token = register_customer(
        username="racket-owner",
        phone_number="+60121110001",
    )
    other_token = register_customer(
        username="other-player",
        phone_number="+60121110002",
    )

    assert client.get("/api/rackets").status_code == 401
    racket = create_racket(owner_token)
    racket_id = str(racket["id"])

    list_response = client.get("/api/rackets", headers=headers(owner_token))
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [racket_id]

    update_response = client.patch(
        f"/api/rackets/{racket_id}",
        headers=headers(owner_token),
        json={"nickname": "Tournament frame", "notes": None},
    )
    assert update_response.status_code == 200
    assert update_response.json()["nickname"] == "Tournament frame"
    assert update_response.json()["notes"] is None

    other_get_response = client.get(
        f"/api/rackets/{racket_id}",
        headers=headers(other_token),
    )
    assert other_get_response.status_code == 404
    other_update_response = client.patch(
        f"/api/rackets/{racket_id}",
        headers=headers(other_token),
        json={"nickname": "Stolen"},
    )
    assert other_update_response.status_code == 404

    booking = create_booking(owner_token, racket_id)
    assert booking["racket_id"] == racket_id
    assert booking["racket_brand"] == "Yonex"
    assert booking["racket_model"] == "Astrox 88D Pro"
    assert booking["check_in_reference"] == (f"CHK-{str(booking['id'])[:8].upper()}")
    assert booking["cancellation_reason"] is None
    assert booking["completion_summary"] is None

    forbidden_booking = client.post(
        "/api/bookings",
        headers=headers(other_token),
        json={
            "string_id": first_string_id(other_token),
            "racket_id": racket_id,
            "requested_tension": 25,
        },
    )
    assert forbidden_booking.status_code == 404

    admin_response = client.get(
        "/api/admin/bookings",
        headers=headers(login_admin()),
    )
    assert admin_response.status_code == 200
    admin_booking = next(
        item for item in admin_response.json()["items"] if item["id"] == booking["id"]
    )
    assert admin_booking["racket_id"] == racket_id
    assert admin_booking["racket_brand"] == "Yonex"
    assert admin_booking["racket_model"] == "Astrox 88D Pro"


def test_feedback_requires_owned_completed_booking_and_is_unique() -> None:
    owner_token = register_customer(
        username="feedback-owner",
        phone_number="+60121110003",
    )
    other_token = register_customer(
        username="feedback-other",
        phone_number="+60121110004",
    )
    admin_token = login_admin()
    racket = create_racket(owner_token)
    racket_id = str(racket["id"])
    completed_booking = create_booking(owner_token, racket_id)
    incomplete_booking = create_booking(owner_token, racket_id)
    booking_id = str(completed_booking["id"])

    early_response = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={"rating": 5, "string_feedback": "Crisp response."},
    )
    assert early_response.status_code == 409

    other_get_response = client.get(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(other_token),
    )
    assert other_get_response.status_code == 404
    other_create_response = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(other_token),
        json={"rating": 5, "string_feedback": "Not my booking."},
    )
    assert other_create_response.status_code == 404

    complete_booking(admin_token, booking_id)

    empty_feedback_response = client.get(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
    )
    assert empty_feedback_response.status_code == 200
    assert empty_feedback_response.json() is None

    invalid_rating = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={"rating": 6, "string_feedback": "Too high."},
    )
    assert invalid_rating.status_code == 422
    invalid_tag = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={"rating": 5, "sentiment_tags": ["invented_tag"]},
    )
    assert invalid_tag.status_code == 422
    too_long = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={"rating": 5, "service_feedback": "x" * 2001},
    )
    assert too_long.status_code == 422

    payload = {
        "rating": 5,
        "string_feedback": "Crisp response with strong repulsion.",
        "service_feedback": "Clear updates and fast turnaround.",
        "sentiment_tags": [
            "crisp_feel",
            "good_communication",
            "fast_turnaround",
            "would_book_again",
        ],
    }
    create_response = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json=payload,
    )
    assert create_response.status_code == 200
    assert create_response.json()["booking_id"] == booking_id
    assert create_response.json()["rating"] == 5
    assert create_response.json()["sentiment_tags"] == payload["sentiment_tags"]

    duplicate_response = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json=payload,
    )
    assert duplicate_response.status_code == 409

    get_response = client.get(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == create_response.json()["id"]

    booking_feedback_response = client.get(
        "/api/admin/feedback",
        headers=headers(admin_token),
        params={"booking_id": booking_id, "limit": 1},
    )
    assert booking_feedback_response.status_code == 200
    assert booking_feedback_response.json()["total"] == 1
    assert booking_feedback_response.json()["items"][0]["booking_id"] == booking_id
    other_booking_feedback_response = client.get(
        "/api/admin/feedback",
        headers=headers(admin_token),
        params={"booking_id": str(incomplete_booking["id"]), "limit": 1},
    )
    assert other_booking_feedback_response.status_code == 200
    assert other_booking_feedback_response.json()["items"] == []

    detail_response = client.get(
        f"/api/rackets/{racket_id}",
        headers=headers(owner_token),
    )
    assert detail_response.status_code == 200
    history = detail_response.json()["service_history"]
    assert [item["booking_id"] for item in history] == [booking_id]
    assert history[0]["feedback"]["id"] == create_response.json()["id"]
    assert str(incomplete_booking["id"]) not in {item["booking_id"] for item in history}
