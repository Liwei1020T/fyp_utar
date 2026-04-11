from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.main import app


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
    order_code = booking_response.json()["order_code"]
    assert order_code.startswith("ORD-")

    my_bookings_response = client.get(
        "/api/bookings",
        headers=headers(customer_token),
    )
    assert my_bookings_response.status_code == 200
    assert my_bookings_response.json()["total"] == 1
    assert my_bookings_response.json()["items"][0]["id"] == booking_id
    assert my_bookings_response.json()["items"][0]["order_code"] == order_code

    admin_token = login_admin()
    admin_list_response = client.get(
        "/api/admin/bookings",
        headers=headers(admin_token),
    )
    assert admin_list_response.status_code == 200
    assert admin_list_response.json()["total"] == 1
    assert admin_list_response.json()["items"][0]["order_code"] == order_code

    admin_search_response = client.get(
        "/api/admin/bookings",
        headers=headers(admin_token),
        params={"search": order_code},
    )
    assert admin_search_response.status_code == 200
    assert admin_search_response.json()["total"] == 1

    update_response = client.patch(
        f"/api/admin/bookings/{booking_id}/status",
        headers=headers(admin_token),
        json={"status": "in_progress"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"
    assert update_response.json()["order_code"] == order_code
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


def test_admin_business_hours_settings_and_slots_flow():
    customer_token = register_customer(phone_number="+60125554444")
    admin_token = login_admin()

    hours_response = client.get(
        "/api/admin/business-hours",
        headers=headers(admin_token),
    )
    assert hours_response.status_code == 200
    assert len(hours_response.json()["days"]) == 7
    assert hours_response.json()["special_closed_dates"] == ["2026-04-14"]

    slots_before_booking = client.get(
        "/api/slots?date=2026-04-06",
        headers=headers(customer_token),
    )
    assert slots_before_booking.status_code == 200
    first_slot = slots_before_booking.json()["items"][0]
    assert first_slot["available_spots"] == first_slot["capacity"]

    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": first_string_id(customer_token),
            "racket_brand": "Yonex",
            "racket_model": "Nanoflare 1000",
            "requested_tension": 25,
            "drop_off_datetime": "2026-04-06T11:00:00",
        },
    )
    assert booking_response.status_code == 200

    slots_after_booking = client.get(
        "/api/admin/slots?date=2026-04-06",
        headers=headers(admin_token),
    )
    assert slots_after_booking.status_code == 200
    updated_slot = next(
        item for item in slots_after_booking.json()["items"] if item["time"] == "11:00"
    )
    assert updated_slot["available_spots"] == updated_slot["capacity"] - 1

    updated_hours_payload = hours_response.json()
    updated_hours_payload["special_closed_dates"] = ["2026-04-06"]
    update_hours_response = client.put(
        "/api/admin/business-hours",
        headers=headers(admin_token),
        json={
            "days": updated_hours_payload["days"],
            "special_closed_dates": updated_hours_payload["special_closed_dates"],
        },
    )
    assert update_hours_response.status_code == 200

    closed_slots_response = client.get(
        "/api/admin/slots?date=2026-04-06",
        headers=headers(admin_token),
    )
    assert closed_slots_response.status_code == 200
    assert closed_slots_response.json()["items"] == []

    settings_response = client.get(
        "/api/admin/store-settings",
        headers=headers(admin_token),
    )
    assert settings_response.status_code == 200
    assert settings_response.json()["store_name"] == "Apex String Lab"

    update_settings_response = client.put(
        "/api/admin/store-settings",
        headers=headers(admin_token),
        json={
            "store_name": "Apex String Lab Express",
            "store_contact": "+60 12-111 2222",
            "support_text": "Admin desk handles booking and string setup support.",
            "payment_notes": "Payments are still reconciled manually in the FYP demo.",
            "booking_notes": "Slots are capped by configured store capacity.",
            "store_policy_text": "Completed bookings are final after collection.",
            "address": "Bukit Jalil, Kuala Lumpur",
        },
    )
    assert update_settings_response.status_code == 200
    assert update_settings_response.json()["store_name"] == "Apex String Lab Express"


def test_admin_check_in_and_service_queue_flow():
    customer_token = register_customer(phone_number="+60126661111")
    admin_token = login_admin()

    first_booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": first_string_id(customer_token),
            "racket_brand": "Victor",
            "racket_model": "Auraspeed",
            "requested_tension": 24,
            "drop_off_datetime": "2026-04-07T11:00:00",
        },
    )
    second_booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": first_string_id(customer_token),
            "racket_brand": "Li-Ning",
            "racket_model": "BladeX",
            "requested_tension": 25,
            "drop_off_datetime": "2026-04-07T12:00:00",
        },
    )
    assert first_booking_response.status_code == 200
    assert second_booking_response.status_code == 200

    booking_id = first_booking_response.json()["id"]
    order_code = first_booking_response.json()["order_code"]
    reference = f"CHK-{booking_id[:8].upper()}"

    lookup_response = client.get(
        f"/api/admin/check-in/lookup?reference={reference}",
        headers=headers(admin_token),
    )
    assert lookup_response.status_code == 200
    assert lookup_response.json()["matched_by"] == "check_in_reference"
    assert lookup_response.json()["booking"]["id"] == booking_id

    order_code_lookup_response = client.get(
        f"/api/admin/check-in/lookup?reference={order_code}",
        headers=headers(admin_token),
    )
    assert order_code_lookup_response.status_code == 200
    assert order_code_lookup_response.json()["matched_by"] == "booking_id"
    assert order_code_lookup_response.json()["booking"]["id"] == booking_id

    check_in_response = client.post(
        "/api/admin/check-in",
        headers=headers(admin_token),
        json={
            "reference": reference,
            "note": "Customer handed over racket at the counter.",
        },
    )
    assert check_in_response.status_code == 200
    assert check_in_response.json()["status"] == "in_progress"
    assert check_in_response.json()["status_history"][-1]["note"] == (
        "Customer handed over racket at the counter."
    )

    queue_response = client.get(
        "/api/admin/service-queue",
        headers=headers(admin_token),
    )
    assert queue_response.status_code == 200
    lanes = {lane["status"]: lane["items"] for lane in queue_response.json()["lanes"]}
    assert len(lanes["in_progress"]) == 1
    assert lanes["in_progress"][0]["booking"]["id"] == booking_id
    assert len(lanes["awaiting_dropoff"]) == 1
    assert lanes["awaiting_dropoff"][0]["queue_position"] == 1


def test_admin_analytics_summary_and_popular_strings():
    customer_token = register_customer(phone_number="+60127773333")
    admin_token = login_admin()

    strings_response = client.get("/api/strings", headers=headers(customer_token))
    assert strings_response.status_code == 200
    string_ids = [item["id"] for item in strings_response.json()["items"][:2]]

    first_booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_ids[0],
            "racket_brand": "Yonex",
            "racket_model": "Astrox 77",
            "requested_tension": 25,
            "drop_off_datetime": "2026-04-08T11:00:00",
        },
    )
    second_booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_ids[0],
            "racket_brand": "Yonex",
            "racket_model": "Arcsaber 11",
            "requested_tension": 24,
            "drop_off_datetime": "2026-04-08T12:00:00",
        },
    )
    third_booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_ids[1],
            "racket_brand": "Victor",
            "racket_model": "Thruster",
            "requested_tension": 26,
            "drop_off_datetime": "2026-04-09T10:00:00",
        },
    )
    assert first_booking_response.status_code == 200
    assert second_booking_response.status_code == 200
    assert third_booking_response.status_code == 200

    first_booking_id = first_booking_response.json()["id"]
    second_booking_id = second_booking_response.json()["id"]

    in_progress_response = client.patch(
        f"/api/admin/bookings/{first_booking_id}/status",
        headers=headers(admin_token),
        json={"status": "in_progress"},
    )
    ready_response = client.patch(
        f"/api/admin/bookings/{first_booking_id}/status",
        headers=headers(admin_token),
        json={"status": "ready_for_collection"},
    )
    completed_response = client.patch(
        f"/api/admin/bookings/{first_booking_id}/status",
        headers=headers(admin_token),
        json={"status": "completed"},
    )
    second_in_progress_response = client.patch(
        f"/api/admin/bookings/{second_booking_id}/status",
        headers=headers(admin_token),
        json={"status": "in_progress"},
    )
    assert in_progress_response.status_code == 200
    assert ready_response.status_code == 200
    assert completed_response.status_code == 200
    assert second_in_progress_response.status_code == 200

    summary_response = client.get(
        "/api/admin/analytics/summary",
        headers=headers(admin_token),
    )
    assert summary_response.status_code == 200
    assert summary_response.json()["weekly_bookings"] == 3
    assert summary_response.json()["awaiting_dropoff_count"] == 1
    assert summary_response.json()["in_progress_count"] == 1
    assert summary_response.json()["ready_for_collection_count"] == 0
    assert summary_response.json()["completed_today"] == 1
    assert summary_response.json()["low_stock_count"] >= 0
    assert string_ids[0] in summary_response.json()["popular_string_ids"]

    popular_strings_response = client.get(
        "/api/admin/analytics/popular-strings?limit=2",
        headers=headers(admin_token),
    )
    assert popular_strings_response.status_code == 200
    assert popular_strings_response.json()[0]["string_id"] == string_ids[0]
    assert popular_strings_response.json()[0]["booking_count"] == 2


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


def test_player_and_admin_can_add_booking_update_photos():
    customer_token = register_customer(
        username="photo-user",
        phone_number="+60125550123",
    )
    string_id = first_string_id(customer_token)
    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Astrox 77",
            "requested_tension": 25,
            "drop_off_datetime": "2026-04-12T10:00:00",
            "notes": "Photo upload test booking.",
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    player_update = client.post(
        f"/api/bookings/{booking_id}/updates",
        headers=headers(customer_token),
        data={"comment": "Frame condition before drop-off.", "photo_type": "racket"},
        files={"photo": ("player-racket.jpg", b"player-photo", "image/jpeg")},
    )
    assert player_update.status_code == 200
    assert player_update.json()["updates"][0]["author_role"] == "customer"
    assert player_update.json()["updates"][0]["photo_url"].startswith(
        "/media/booking-updates/"
    )
    assert player_update.json()["updates"][0]["photo_type"] == "racket"

    admin_token = login_admin()
    admin_update = client.post(
        f"/api/admin/bookings/{booking_id}/updates",
        headers=headers(admin_token),
        data={
            "comment": "Admin received the racket photo.",
            "photo_type": "service_progress",
        },
        files={"photo": ("admin-racket.png", b"admin-photo", "image/png")},
    )
    assert admin_update.status_code == 200
    updates = admin_update.json()["updates"]
    assert [item["author_role"] for item in updates] == ["customer", "admin"]
    assert updates[-1]["comment"] == "Admin received the racket photo."
    assert updates[-1]["photo_type"] == "service_progress"

    admin_photo_update = client.post(
        f"/api/admin/bookings/{booking_id}/photos",
        headers=headers(admin_token),
        data={"comment": "Reference photo before collection.", "photo_type": "other"},
        files={"photo": ("collection.webp", b"admin-photo-2", "image/webp")},
    )
    assert admin_photo_update.status_code == 200
    updates = admin_photo_update.json()["updates"]
    assert updates[-1]["author_role"] == "admin"
    assert updates[-1]["comment"] == "Reference photo before collection."
    assert updates[-1]["photo_type"] == "other"
    assert updates[-1]["photo_url"].startswith("/media/booking-updates/")

    player_detail = client.get(
        f"/api/bookings/{booking_id}",
        headers=headers(customer_token),
    )
    assert player_detail.status_code == 200
    assert len(player_detail.json()["updates"]) == 3
