from fastapi.testclient import TestClient
from datetime import date
from datetime import timedelta
from sqlalchemy import select

from app.db.models import Booking
from app.db.models import BookingStatusHistory
from app.db.session import SessionLocal
from app.main import app


client = TestClient(app)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_function():
    from app.services.auth_service import auth_service
    from app.services.booking_service import booking_service
    from app.services.string_service import string_service

    auth_service.reset()
    booking_service.reset()
    string_service.reset()


def _register_customer_token(phone_number: str = "0123456789") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": phone_number,
            "password": "secret123",
        },
    )
    return response.json()["data"]["access_token"]


def _admin_token() -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0190000000",
            "password": "admin123",
        },
    )
    return response.json()["data"]["access_token"]


def _first_string_id(customer_token: str) -> str:
    response = client.get("/api/v1/strings", headers=_headers(customer_token))
    return response.json()["data"][0]["id"]


def test_customer_can_create_booking():
    customer_token = _register_customer_token()

    response = client.post(
        "/api/v1/bookings",
        json={
            "string_id": _first_string_id(customer_token),
            "racket_brand": "Yonex",
            "racket_model": "Astrox 88D",
            "requested_tension": 25,
        },
        headers=_headers(customer_token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "pending"
    assert response.json()["data"]["string_name"] == "Yonex BG80"

    booking_id = response.json()["data"]["id"]
    with SessionLocal() as db:
        booking = db.execute(
            select(Booking).where(Booking.id == booking_id)
        ).scalar_one_or_none()

    assert booking is not None
    assert booking.status == "pending"


def test_customer_can_get_own_bookings():
    customer_token = _register_customer_token()

    create_response = client.post(
        "/api/v1/bookings",
        json={"string_id": _first_string_id(customer_token)},
        headers=_headers(customer_token),
    )

    booking_id = create_response.json()["data"]["id"]
    list_response = client.get("/api/v1/bookings/me", headers=_headers(customer_token))
    detail_response = client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=_headers(customer_token),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["string_name"] == "Yonex BG80"
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == booking_id
    assert detail_response.json()["data"]["string_name"] == "Yonex BG80"


def test_admin_can_list_and_update_booking_status():
    customer_token = _register_customer_token()
    admin_token = _admin_token()

    create_response = client.post(
        "/api/v1/bookings",
        json={"string_id": _first_string_id(customer_token)},
        headers=_headers(customer_token),
    )
    booking_id = create_response.json()["data"]["id"]

    list_response = client.get("/api/v1/admin/bookings", headers=_headers(admin_token))
    update_response = client.patch(
        f"/api/v1/admin/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers=_headers(admin_token),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["string_name"] == "Yonex BG80"
    detail_response = client.get(
        f"/api/v1/admin/bookings/{booking_id}",
        headers=_headers(admin_token),
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == booking_id
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "confirmed"
    assert update_response.json()["data"]["string_name"] == "Yonex BG80"

    with SessionLocal() as db:
        booking = db.execute(
            select(Booking).where(Booking.id == booking_id)
        ).scalar_one_or_none()

    assert booking is not None
    assert booking.status == "confirmed"


def test_booking_history_is_written():
    customer_token = _register_customer_token()
    admin_token = _admin_token()

    create_response = client.post(
        "/api/v1/bookings",
        json={"string_id": _first_string_id(customer_token)},
        headers=_headers(customer_token),
    )
    booking_id = create_response.json()["data"]["id"]

    client.patch(
        f"/api/v1/admin/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers=_headers(admin_token),
    )

    with SessionLocal() as db:
        history = (
            db.execute(
                select(BookingStatusHistory).where(
                    BookingStatusHistory.booking_id == booking_id
                )
            )
            .scalars()
            .all()
        )

    assert len(history) == 2
    assert history[0].new_status == "pending"
    assert history[1].new_status == "confirmed"


def test_booking_status_rejects_illegal_transition():
    customer_token = _register_customer_token()
    admin_token = _admin_token()

    create_response = client.post(
        "/api/v1/bookings",
        json={"string_id": _first_string_id(customer_token)},
        headers=_headers(customer_token),
    )
    booking_id = create_response.json()["data"]["id"]

    invalid_response = client.patch(
        f"/api/v1/admin/bookings/{booking_id}/status",
        json={"status": "picked_up"},
        headers=_headers(admin_token),
    )

    assert invalid_response.status_code == 409
    assert invalid_response.json()["detail"] == "Invalid booking status transition"


def test_customer_cannot_create_booking_for_unknown_string():
    customer_token = _register_customer_token()

    response = client.post(
        "/api/v1/bookings",
        json={"string_id": "missing-string"},
        headers=_headers(customer_token),
    )

    assert response.status_code == 404


def test_customer_cannot_create_booking_for_inactive_string():
    customer_token = _register_customer_token()
    admin_token = _admin_token()
    string_id = _first_string_id(customer_token)

    client.delete(
        f"/api/v1/admin/strings/{string_id}",
        headers=_headers(admin_token),
    )
    response = client.post(
        "/api/v1/bookings",
        json={"string_id": string_id},
        headers=_headers(customer_token),
    )

    assert response.status_code == 409


def test_customer_cannot_create_booking_in_the_past():
    customer_token = _register_customer_token()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    response = client.post(
        "/api/v1/bookings",
        json={
            "string_id": _first_string_id(customer_token),
            "appointment_date": yesterday,
        },
        headers=_headers(customer_token),
    )

    assert response.status_code == 422


def test_admin_bookings_support_status_filter_and_pagination():
    customer_token = _register_customer_token()
    admin_token = _admin_token()

    first_booking = client.post(
        "/api/v1/bookings",
        json={"string_id": _first_string_id(customer_token)},
        headers=_headers(customer_token),
    ).json()["data"]["id"]
    second_booking = client.post(
        "/api/v1/bookings",
        json={
            "string_id": _first_string_id(customer_token),
            "racket_model": "Nanoflare 1000",
        },
        headers=_headers(customer_token),
    ).json()["data"]["id"]

    client.patch(
        f"/api/v1/admin/bookings/{first_booking}/status",
        json={"status": "confirmed"},
        headers=_headers(admin_token),
    )

    response = client.get(
        "/api/v1/admin/bookings?status=confirmed&limit=1&offset=0",
        headers=_headers(admin_token),
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["id"] == first_booking
    assert response.json()["pagination"]["total"] == 1
    assert second_booking != first_booking


def test_pending_booking_can_be_rejected_by_admin():
    customer_token = _register_customer_token()
    admin_token = _admin_token()

    booking_id = client.post(
        "/api/v1/bookings",
        json={"string_id": _first_string_id(customer_token)},
        headers=_headers(customer_token),
    ).json()["data"]["id"]

    response = client.patch(
        f"/api/v1/admin/bookings/{booking_id}/status",
        json={"status": "rejected"},
        headers=_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rejected"
