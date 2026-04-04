from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from stringsense_backend.core.config import get_settings
from stringsense_backend.db.models import PasswordResetCode
from stringsense_backend.db.session import SessionLocal
from stringsense_backend.main import app


client = TestClient(app)


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_customer(
    *,
    username: str = "tanweijie",
    phone_number: str = "+60123456789",
    password: str = "secret123",
) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "phone_number": phone_number,
            "password": password,
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


def enable_password_reset_preview(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)


def test_auth_profile_booking_and_admin_status_flow():
    customer_token = register_customer()

    me_response = client.get("/api/auth/me", headers=headers(customer_token))
    assert me_response.status_code == 200
    assert me_response.json()["phone_number"] == "+60123456789"

    upsert_profile_response = client.put(
        "/api/profile",
        headers=headers(customer_token),
        json={
            "skill_level": "intermediate",
            "playing_style": "attacking",
            "budget_min": 40,
            "budget_max": 80,
            "preferred_tension": 25,
            "game_type": "doubles",
            "frequency_per_week": 3,
            "pref_attack": 5,
            "pref_comfort": 3,
            "pref_control": 4,
            "pref_durability": 4,
            "pref_elasticity": 5,
            "pref_sound": 3,
            "pref_string_movement": 4,
            "pref_tension_retention": 4,
            "pref_value_for_money": 3,
        },
    )
    assert upsert_profile_response.status_code == 200
    assert upsert_profile_response.json()["playing_style"] == "attacking"

    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": first_string_id(customer_token),
            "racket_brand": "Yonex",
            "racket_model": "Astrox 88D",
            "requested_tension": 25,
        },
    )
    assert booking_response.status_code == 200
    assert booking_response.json()["status"] == "awaiting_dropoff"
    booking_id = booking_response.json()["id"]

    my_bookings_response = client.get(
        "/api/bookings",
        headers=headers(customer_token),
    )
    assert my_bookings_response.status_code == 200
    assert my_bookings_response.json()["total"] == 1
    assert my_bookings_response.json()["items"][0]["id"] == booking_id

    admin_token = login_admin()
    admin_list_response = client.get(
        "/api/admin/bookings",
        headers=headers(admin_token),
    )
    assert admin_list_response.status_code == 200
    assert admin_list_response.json()["total"] == 1

    update_response = client.patch(
        f"/api/admin/bookings/{booking_id}/status",
        headers=headers(admin_token),
        json={"status": "in_progress"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"
    assert len(update_response.json()["status_history"]) == 2


def test_customer_cannot_access_admin_booking_routes():
    customer_token = register_customer()

    response = client.get(
        "/api/admin/bookings",
        headers=headers(customer_token),
    )

    assert response.status_code == 403
    assert (
        response.json()["error"]["message"]
        == "Insufficient permissions for this resource"
    )


def test_recommendations_logs_and_admin_string_controls():
    customer_token = register_customer(phone_number="+60128888888")
    admin_token = login_admin()

    profile_response = client.put(
        "/api/profile",
        headers=headers(customer_token),
        json={
            "skill_level": "advanced",
            "playing_style": "balanced",
            "budget_min": 30,
            "budget_max": 90,
            "preferred_tension": 26,
            "game_type": "doubles",
            "frequency_per_week": 4,
            "pref_attack": 5,
            "pref_comfort": 2,
            "pref_control": 4,
            "pref_durability": 3,
            "pref_elasticity": 5,
            "pref_sound": 4,
            "pref_string_movement": 3,
            "pref_tension_retention": 4,
            "pref_value_for_money": 2,
        },
    )
    assert profile_response.status_code == 200

    recommendation_response = client.post(
        "/api/recommendations/profile",
        headers=headers(customer_token),
        json={"top_n": 3},
    )
    assert recommendation_response.status_code == 200
    assert (
        recommendation_response.json()["algorithm_version"]
        == "unified_python_rule_engine_v1"
    )
    assert len(recommendation_response.json()["results"]) == 3

    log_response = client.get(
        "/api/admin/recommendations/logs",
        headers=headers(admin_token),
    )
    assert log_response.status_code == 200
    assert log_response.json()["total"] == 1
    assert log_response.json()["items"][0]["phone_number"] == "+60128888888"

    removed_duplicate_route = client.get(
        "/api/recommendations/logs",
        headers=headers(admin_token),
    )
    assert removed_duplicate_route.status_code == 404

    admin_strings = client.get(
        "/api/admin/strings",
        headers=headers(admin_token),
    )
    assert admin_strings.status_code == 200
    string_item = admin_strings.json()["items"][0]

    update_string = client.put(
        f"/api/admin/strings/{string_item['id']}",
        headers=headers(admin_token),
        json={
            "brand": string_item["brand"],
            "model_name": string_item["model_name"],
            "price_rm": 55,
        },
    )
    assert update_string.status_code == 200
    assert update_string.json()["price_rm"] == 55

    deactivate_string = client.delete(
        f"/api/admin/strings/{string_item['id']}",
        headers=headers(admin_token),
    )
    assert deactivate_string.status_code == 200
    assert deactivate_string.json()["is_active"] is False


def test_admin_inventory_string_update_controls_public_availability():
    customer_token = register_customer(phone_number="+60127774444")
    admin_token = login_admin()
    string_id = first_string_id(customer_token)

    inventory_response = client.get(
        "/api/admin/inventory/strings",
        headers=headers(admin_token),
    )
    assert inventory_response.status_code == 200
    matching_item = next(
        item for item in inventory_response.json()["items"] if item["id"] == string_id
    )
    assert matching_item["stock_level"] == 8
    assert matching_item["availability"] == "in_stock"

    low_stock_response = client.patch(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
        json={
            "price_rm": 48,
            "stock_level": 3,
            "admin_note": "Reserve 2 packs for walk-in customers.",
        },
    )
    assert low_stock_response.status_code == 200
    assert low_stock_response.json()["price_rm"] == 48
    assert low_stock_response.json()["stock_level"] == 3
    assert low_stock_response.json()["availability"] == "low_stock"
    assert (
        low_stock_response.json()["admin_note"]
        == "Reserve 2 packs for walk-in customers."
    )

    out_of_stock_response = client.patch(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
        json={"stock_level": 0},
    )
    assert out_of_stock_response.status_code == 200
    assert out_of_stock_response.json()["stock_level"] == 0
    assert out_of_stock_response.json()["availability"] == "out_of_stock"
    assert out_of_stock_response.json()["is_active"] is False

    public_lookup = client.get(
        f"/api/strings/{string_id}",
        headers=headers(customer_token),
    )
    assert public_lookup.status_code == 404


def test_request_password_reset_is_generic_for_unknown_phone(monkeypatch):
    enable_password_reset_preview(monkeypatch)

    response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60127777777"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent if the account exists"
    assert response.json()["dev_code_preview"] is None


def test_customer_can_reset_password_with_verification_code(monkeypatch):
    enable_password_reset_preview(monkeypatch)
    register_customer()

    request_code_response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60123456789"},
    )
    assert request_code_response.status_code == 200
    verification_code = request_code_response.json()["dev_code_preview"]
    assert verification_code is not None

    reset_response = client.post(
        "/api/auth/forgot-password/reset",
        json={
            "phone_number": "+60123456789",
            "verification_code": verification_code,
            "new_password": "newpass456",
        },
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "Password reset successful"

    old_password_login = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60123456789",
            "password": "secret123",
        },
    )
    assert old_password_login.status_code == 401

    new_password_login = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60123456789",
            "password": "newpass456",
        },
    )
    assert new_password_login.status_code == 200


def test_reset_password_rejects_reused_verification_code(monkeypatch):
    enable_password_reset_preview(monkeypatch)
    register_customer()

    request_code_response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60123456789"},
    )
    verification_code = request_code_response.json()["dev_code_preview"]

    first_reset_response = client.post(
        "/api/auth/forgot-password/reset",
        json={
            "phone_number": "+60123456789",
            "verification_code": verification_code,
            "new_password": "newpass456",
        },
    )
    second_reset_response = client.post(
        "/api/auth/forgot-password/reset",
        json={
            "phone_number": "+60123456789",
            "verification_code": verification_code,
            "new_password": "newpass789",
        },
    )

    assert first_reset_response.status_code == 200
    assert second_reset_response.status_code == 400
    assert (
        second_reset_response.json()["error"]["message"]
        == "Invalid or expired verification code"
    )


def test_reset_password_enforces_attempt_limit(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)
    monkeypatch.setattr(settings, "password_reset_code_max_attempts", 2)
    register_customer()

    request_code_response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60123456789"},
    )
    assert request_code_response.status_code == 200

    for _ in range(2):
        response = client.post(
            "/api/auth/forgot-password/reset",
            json={
                "phone_number": "+60123456789",
                "verification_code": "000000",
                "new_password": "newpass456",
            },
        )
        assert response.status_code == 400

    limit_response = client.post(
        "/api/auth/forgot-password/reset",
        json={
            "phone_number": "+60123456789",
            "verification_code": "000000",
            "new_password": "newpass456",
        },
    )
    assert limit_response.status_code == 400
    assert (
        limit_response.json()["error"]["message"]
        == "Verification code attempt limit exceeded"
    )

    with SessionLocal() as db:
        reset_code = db.execute(select(PasswordResetCode)).scalar_one()

    assert reset_code.attempt_count == 2


def test_admin_reject_requires_note_and_persists_history_note():
    customer_token = register_customer(phone_number="+60126666666")
    admin_token = login_admin()

    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": first_string_id(customer_token),
            "racket_brand": "Li-Ning",
            "racket_model": "Halbertec 8000",
            "requested_tension": 24,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    missing_note_response = client.patch(
        f"/api/admin/bookings/{booking_id}/status",
        headers=headers(admin_token),
        json={"status": "rejected"},
    )
    assert missing_note_response.status_code == 422

    rejection_response = client.patch(
        f"/api/admin/bookings/{booking_id}/status",
        headers=headers(admin_token),
        json={
            "status": "rejected",
            "note": "Customer requested a drop-off slot outside business hours.",
        },
    )
    assert rejection_response.status_code == 200
    assert rejection_response.json()["status"] == "rejected"
    assert (
        rejection_response.json()["latest_admin_note"]
        == "Customer requested a drop-off slot outside business hours."
    )
    assert rejection_response.json()["status_history"][-1]["note"] == (
        "Customer requested a drop-off slot outside business hours."
    )
