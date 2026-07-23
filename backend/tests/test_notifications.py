from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models.notification import NotificationRead
from app.adapters.persistence.sqlalchemy.models.recommendation_log import (
    RecommendationRun,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.main import app


client = TestClient(app)


@dataclass(frozen=True)
class NotificationActivity:
    owner_token: str
    owner_id: str
    other_token: str


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(phone_number: str) -> tuple[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"user-{phone_number[-4:]}",
            "phone_number": phone_number,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"], response.json()["user_id"]


def _admin_token() -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60190000000",
            "password": "admin1234",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def notification_activity() -> NotificationActivity:
    owner_token, owner_id = _register("+60127770001")
    other_token, _ = _register("+60127770002")
    admin_token = _admin_token()

    strings_response = client.get("/api/strings", headers=_headers(owner_token))
    assert strings_response.status_code == 200
    string_id = strings_response.json()["items"][0]["id"]

    booking_response = client.post(
        "/api/bookings",
        headers=_headers(owner_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Astrox 88D",
            "requested_tension": 25,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    status_response = client.patch(
        f"/api/admin/bookings/{booking_id}/status",
        headers=_headers(admin_token),
        json={"status": "in_progress", "note": "Stringing has started."},
    )
    assert status_response.status_code == 200

    update_response = client.post(
        f"/api/admin/bookings/{booking_id}/updates",
        headers=_headers(admin_token),
        data={"comment": "Your racket passed the frame inspection."},
    )
    assert update_response.status_code == 200

    support_response = client.post(
        f"/api/bookings/{booking_id}/support",
        headers=_headers(owner_token),
    )
    assert support_response.status_code == 200
    chat_response = client.post(
        f"/api/admin/conversations/{booking_id}/messages",
        headers=_headers(admin_token),
        json={"body": "Your pickup timing is confirmed."},
    )
    assert chat_response.status_code == 200

    top_up_response = client.post(
        "/api/wallet/top-ups",
        headers=_headers(owner_token),
        json={"amount": 50, "method": "online_banking"},
    )
    assert top_up_response.status_code == 200
    verify_response = client.patch(
        f"/api/admin/payments/{top_up_response.json()['id']}",
        headers=_headers(admin_token),
        json={"status": "paid"},
    )
    assert verify_response.status_code == 200

    with SessionLocal() as db:
        db.add(
            RecommendationRun(
                user_id=owner_id,
                algorithm_version="notification-test",
                request_snapshot={},
                profile_snapshot={},
            )
        )
        db.commit()

    return NotificationActivity(
        owner_token=owner_token,
        owner_id=owner_id,
        other_token=other_token,
    )


def test_notifications_require_authentication() -> None:
    assert client.get("/api/notifications").status_code == 401
    assert (
        client.patch(
            "/api/notifications/read",
            json={"event_ids": ["booking-status:not-owned"]},
        ).status_code
        == 401
    )


def test_notification_feed_derives_owned_events_and_applies_preferences(
    notification_activity: NotificationActivity,
) -> None:
    response = client.get(
        "/api/notifications",
        headers=_headers(notification_activity.owner_token),
    )

    assert response.status_code == 200
    events = response.json()
    assert {event["category"] for event in events} == {
        "booking",
        "service",
        "chat",
        "payment",
        "recommendation",
    }
    assert all(event["user_id"] == notification_activity.owner_id for event in events)
    assert all(event["read"] is False for event in events)
    assert [event["created_at"] for event in events] == sorted(
        (event["created_at"] for event in events),
        reverse=True,
    )
    assert any(event["id"].startswith("booking-status:") for event in events)
    assert any(event["id"].startswith("booking-update:") for event in events)
    assert any(event["id"].startswith("conversation-update:") for event in events)
    assert any(event["id"].endswith(":paid") for event in events)
    assert any(event["id"].startswith("recommendation:") for event in events)

    preferences = client.get(
        "/api/notifications/preferences",
        headers=_headers(notification_activity.owner_token),
    ).json()
    preferences["service"] = False
    preferences["chat"] = False
    preferences["payment"] = False
    update_response = client.put(
        "/api/notifications/preferences",
        headers=_headers(notification_activity.owner_token),
        json=preferences,
    )
    assert update_response.status_code == 200

    filtered_response = client.get(
        "/api/notifications",
        headers=_headers(notification_activity.owner_token),
    )
    assert filtered_response.status_code == 200
    assert {event["category"] for event in filtered_response.json()} == {
        "booking",
        "recommendation",
    }


def test_mark_read_persists_and_rejects_foreign_or_unbounded_ids(
    notification_activity: NotificationActivity,
) -> None:
    events = client.get(
        "/api/notifications",
        headers=_headers(notification_activity.owner_token),
    ).json()
    event_id = next(event["id"] for event in events if event["category"] == "booking")

    mark_response = client.patch(
        "/api/notifications/read",
        headers=_headers(notification_activity.owner_token),
        json={"event_ids": [event_id, event_id]},
    )
    assert mark_response.status_code == 200
    assert mark_response.json() == {
        "marked_count": 1,
        "marked_read_ids": [event_id],
    }

    refreshed_events = client.get(
        "/api/notifications",
        headers=_headers(notification_activity.owner_token),
    ).json()
    assert next(event for event in refreshed_events if event["id"] == event_id)["read"]
    with SessionLocal() as db:
        marker = db.scalar(
            select(NotificationRead).where(
                NotificationRead.user_id == notification_activity.owner_id,
                NotificationRead.event_id == event_id,
            )
        )
        assert marker is not None

    foreign_response = client.patch(
        "/api/notifications/read",
        headers=_headers(notification_activity.other_token),
        json={"event_ids": [event_id]},
    )
    assert foreign_response.status_code == 404

    oversized_response = client.patch(
        "/api/notifications/read",
        headers=_headers(notification_activity.owner_token),
        json={"event_ids": [f"booking-status:{'x' * 160}"]},
    )
    assert oversized_response.status_code == 422

    too_many_response = client.patch(
        "/api/notifications/read",
        headers=_headers(notification_activity.owner_token),
        json={"event_ids": [f"booking-status:{index}" for index in range(101)]},
    )
    assert too_many_response.status_code == 422
    assert (
        client.get(
            "/api/notifications?limit=201",
            headers=_headers(notification_activity.owner_token),
        ).status_code
        == 422
    )
