from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_customer(phone_number: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"player-{phone_number[-4:]}",
            "phone_number": phone_number,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _login_admin() -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60190000000",
            "password": "admin1234",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_booking(token: str) -> str:
    strings_response = client.get("/api/strings", headers=_headers(token))
    assert strings_response.status_code == 200
    booking_response = client.post(
        "/api/bookings",
        headers=_headers(token),
        json={"string_id": strings_response.json()["items"][0]["id"]},
    )
    assert booking_response.status_code == 200
    return booking_response.json()["id"]


def test_booking_conversation_lifecycle_and_thread_dto():
    player_token = _register_customer("+60121110001")
    admin_token = _login_admin()
    booking_id = _create_booking(player_token)
    _create_booking(player_token)

    service_update = client.post(
        f"/api/bookings/{booking_id}/updates",
        headers=_headers(player_token),
        data={"comment": "Racket handed to the service counter."},
    )
    assert service_update.status_code == 200

    empty_player_list = client.get(
        "/api/conversations",
        headers=_headers(player_token),
    )
    assert empty_player_list.status_code == 200
    assert empty_player_list.json() == []

    requested = client.post(
        f"/api/bookings/{booking_id}/support",
        headers=_headers(player_token),
    )
    assert requested.status_code == 200
    thread = requested.json()
    assert thread["id"] == booking_id
    assert thread["booking_id"] == booking_id
    assert thread["state"] == "waiting_admin"
    assert thread["support_requested_at"] is not None
    assert thread["player_last_read_at"] is None
    assert thread["admin_last_read_at"] is None
    assert thread["messages"] == []

    requested_again = client.post(
        f"/api/bookings/{booking_id}/support",
        headers=_headers(player_token),
    )
    assert requested_again.status_code == 200
    assert (
        requested_again.json()["support_requested_at"]
        == (thread["support_requested_at"])
    )

    player_message = client.post(
        f"/api/conversations/{booking_id}/messages",
        headers=_headers(player_token),
        json={"body": "  When will my racket be ready?  "},
    )
    assert player_message.status_code == 200
    assert player_message.json()["messages"][0]["body"] == (
        "When will my racket be ready?"
    )
    assert player_message.json()["messages"][0]["author_role"] == "customer"
    unread_summary = client.get(
        "/api/admin/analytics/summary",
        headers=_headers(admin_token),
    )
    assert unread_summary.json()["unread_chats"] == 1

    player_list = client.get(
        "/api/conversations",
        headers=_headers(player_token),
    )
    admin_list = client.get(
        "/api/admin/conversations",
        headers=_headers(admin_token),
    )
    assert len(player_list.json()) == 1
    assert len(admin_list.json()) == 1

    admin_message = client.post(
        f"/api/admin/conversations/{booking_id}/messages",
        headers=_headers(admin_token),
        json={"body": "It will be ready tomorrow."},
    )
    assert admin_message.status_code == 200
    assert admin_message.json()["state"] == "admin_joined"
    assert [item["author_role"] for item in admin_message.json()["messages"]] == [
        "customer",
        "admin",
    ]

    player_read = client.post(
        f"/api/conversations/{booking_id}/read",
        headers=_headers(player_token),
    )
    admin_read = client.post(
        f"/api/admin/conversations/{booking_id}/read",
        headers=_headers(admin_token),
    )
    assert player_read.json()["player_last_read_at"] is not None
    assert admin_read.json()["admin_last_read_at"] is not None
    read_summary = client.get(
        "/api/admin/analytics/summary",
        headers=_headers(admin_token),
    )
    assert read_summary.json()["unread_chats"] == 0

    resolved = client.post(
        f"/api/admin/conversations/{booking_id}/resolve",
        headers=_headers(admin_token),
    )
    closed = client.post(
        f"/api/admin/conversations/{booking_id}/close",
        headers=_headers(admin_token),
    )
    assert resolved.json()["state"] == "resolved"
    assert closed.json()["state"] == "closed"

    reopened = client.post(
        f"/api/bookings/{booking_id}/support",
        headers=_headers(player_token),
    )
    assert reopened.status_code == 200
    assert reopened.json()["state"] == "waiting_admin"


def test_conversation_routes_enforce_booking_ownership_and_admin_role():
    owner_token = _register_customer("+60121110002")
    other_token = _register_customer("+60121110003")
    booking_id = _create_booking(owner_token)

    requested = client.post(
        f"/api/bookings/{booking_id}/support",
        headers=_headers(owner_token),
    )
    assert requested.status_code == 200

    assert (
        client.post(
            f"/api/bookings/{booking_id}/support",
            headers=_headers(other_token),
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/conversations/{booking_id}",
            headers=_headers(other_token),
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/conversations/{booking_id}/messages",
            headers=_headers(other_token),
            json={"body": "Unauthorized"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/conversations/{booking_id}/read",
            headers=_headers(other_token),
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/admin/conversations",
            headers=_headers(owner_token),
        ).status_code
        == 403
    )
    assert client.get("/api/conversations").status_code == 401


def test_conversation_message_length_validation_and_closed_guard():
    player_token = _register_customer("+60121110004")
    admin_token = _login_admin()
    booking_id = _create_booking(player_token)
    client.post(
        f"/api/bookings/{booking_id}/support",
        headers=_headers(player_token),
    )

    for body in ("", "   ", "x" * 2001):
        response = client.post(
            f"/api/conversations/{booking_id}/messages",
            headers=_headers(player_token),
            json={"body": body},
        )
        assert response.status_code == 422

    maximum_length = client.post(
        f"/api/conversations/{booking_id}/messages",
        headers=_headers(player_token),
        json={"body": "x" * 2000},
    )
    assert maximum_length.status_code == 200

    closed = client.post(
        f"/api/admin/conversations/{booking_id}/close",
        headers=_headers(admin_token),
    )
    assert closed.status_code == 200
    blocked_message = client.post(
        f"/api/conversations/{booking_id}/messages",
        headers=_headers(player_token),
        json={"body": "Please reopen"},
    )
    assert blocked_message.status_code == 409


def test_general_support_is_available_without_a_booking_and_reuses_thread():
    player_token = _register_customer("+60121110005")
    other_token = _register_customer("+60121110006")
    admin_token = _login_admin()

    requested = client.post(
        "/api/conversations/support",
        headers=_headers(player_token),
    )
    assert requested.status_code == 200
    thread = requested.json()
    assert thread["id"]
    assert thread["booking_id"] is None
    assert thread["state"] == "waiting_admin"
    conversation_id = thread["id"]

    requested_again = client.post(
        "/api/conversations/support",
        headers=_headers(player_token),
    )
    assert requested_again.status_code == 200
    assert requested_again.json()["id"] == conversation_id

    message = client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=_headers(player_token),
        json={"body": "I need help choosing a string."},
    )
    assert message.status_code == 200
    assert message.json()["booking_id"] is None
    assert message.json()["messages"][0]["author_role"] == "customer"

    assert (
        client.get(
            f"/api/conversations/{conversation_id}",
            headers=_headers(other_token),
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/admin/conversations",
            headers=_headers(admin_token),
        ).json()[0]["id"]
        == conversation_id
    )
    assert (
        client.get(
            "/api/admin/analytics/summary",
            headers=_headers(admin_token),
        ).json()["unread_chats"]
        == 1
    )

    reply = client.post(
        f"/api/admin/conversations/{conversation_id}/messages",
        headers=_headers(admin_token),
        json={"body": "The shop desk can help with that."},
    )
    assert reply.status_code == 200
    assert reply.json()["state"] == "admin_joined"

    notifications = client.get(
        "/api/notifications",
        headers=_headers(player_token),
    )
    assert notifications.status_code == 200
    assert any(
        item["id"]
        == f"general-conversation-update:{reply.json()['messages'][-1]['id']}"
        for item in notifications.json()
    )

    closed = client.post(
        f"/api/admin/conversations/{conversation_id}/close",
        headers=_headers(admin_token),
    )
    assert closed.status_code == 200
    reopened = client.post(
        "/api/conversations/support",
        headers=_headers(player_token),
    )
    assert reopened.status_code == 200
    assert reopened.json()["id"] == conversation_id
    assert reopened.json()["state"] == "waiting_admin"
