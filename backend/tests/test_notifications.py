from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models.notification import (
    NotificationDelivery,
)
from app.adapters.persistence.sqlalchemy.models.notification import NotificationRead
from app.adapters.persistence.sqlalchemy.models.recommendation_log import (
    RecommendationRun,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.main import app
from app.entrypoints.api.routes import admin_engagement_routes


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


def test_admin_push_delivery_returns_persisted_outcome_and_resends_once(
    monkeypatch,
    notification_activity: NotificationActivity,
) -> None:
    token_response = client.post(
        "/api/devices/push-token",
        headers=_headers(notification_activity.owner_token),
        json={
            "token": "ExponentPushToken[transaction-test]",
            "platform": "ios",
        },
    )
    assert token_response.status_code == 200

    settings = get_settings()
    monkeypatch.setattr(settings, "expo_push_enabled", True)
    monkeypatch.setattr(settings, "expo_push_endpoint", "https://expo.test/send")
    observed_statuses: list[str] = []
    provider_calls: list[object] = []

    class FakeResponse:
        def __init__(self, body: bytes) -> None:
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def read(self) -> bytes:
            return self.body

    def fake_urlopen(request, timeout: int):
        assert request.full_url == "https://expo.test/send"
        assert timeout == 5
        provider_calls.append(request)
        with SessionLocal() as db:
            notification = db.scalar(
                select(NotificationDelivery).order_by(
                    NotificationDelivery.created_at.desc()
                )
            )
            assert notification is not None
            observed_statuses.append(notification.status)
        if len(provider_calls) == 1:
            return FakeResponse(b'{"data":{"status":"ok","id":"ticket-1"}}')
        return FakeResponse(
            b'{"data":{"status":"error","message":"provider rejected"}}'
        )

    monkeypatch.setattr(admin_engagement_routes.urllib_request, "urlopen", fake_urlopen)
    response = client.post(
        "/api/admin/notifications",
        headers=_headers(_admin_token()),
        json={
            "user_id": notification_activity.owner_id,
            "category": "service",
            "title": "Delivery check",
            "body": "The provider should run after commit.",
            "route": "/player/notifications",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert response.json()["provider_message"] == "ticket-1"
    assert observed_statuses == ["pending"]
    notification_id = response.json()["id"]
    with SessionLocal() as db:
        notification = db.get(NotificationDelivery, notification_id)
        assert notification is not None
        assert notification.status == "sent"
        assert notification.attempts == 1
        assert notification.provider_message == "ticket-1"

    resend_response = client.post(
        f"/api/admin/notifications/{notification_id}/resend",
        headers=_headers(_admin_token()),
    )
    assert resend_response.status_code == 200
    assert resend_response.json()["status"] == "failed"
    assert resend_response.json()["provider_message"] == "provider rejected"
    assert observed_statuses == ["pending", "pending"]
    assert len(provider_calls) == 2
    with SessionLocal() as db:
        notification = db.get(NotificationDelivery, notification_id)
        assert notification is not None
        assert notification.status == "failed"
        assert notification.attempts == 2


def test_admin_push_delivery_skips_provider_when_initial_commit_fails(
    monkeypatch,
    notification_activity: NotificationActivity,
) -> None:
    token_response = client.post(
        "/api/devices/push-token",
        headers=_headers(notification_activity.owner_token),
        json={
            "token": "ExponentPushToken[commit-failure-test]",
            "platform": "ios",
        },
    )
    assert token_response.status_code == 200

    settings = get_settings()
    monkeypatch.setattr(settings, "expo_push_enabled", True)
    monkeypatch.setattr(settings, "expo_push_endpoint", "https://expo.test/send")
    provider_calls: list[object] = []

    def fake_urlopen(*args, **kwargs):
        provider_calls.append((args, kwargs))
        raise AssertionError("provider must not run before the initial commit")

    def fail_commit(_: Session) -> None:
        raise RuntimeError("forced initial notification commit failure")

    monkeypatch.setattr(admin_engagement_routes.urllib_request, "urlopen", fake_urlopen)
    admin_token = _admin_token()
    monkeypatch.setattr(Session, "commit", fail_commit)

    with pytest.raises(
        RuntimeError, match="forced initial notification commit failure"
    ):
        client.post(
            "/api/admin/notifications",
            headers=_headers(admin_token),
            json={
                "user_id": notification_activity.owner_id,
                "category": "service",
                "title": "Commit failure check",
                "body": "Provider must not run.",
            },
        )

    assert provider_calls == []
