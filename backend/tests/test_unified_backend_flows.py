from __future__ import annotations

import hashlib
import hmac
from urllib.parse import parse_qs
from urllib.parse import unquote
from urllib.parse import urlparse

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import UserPreferenceMatrix
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.main import app
from app.shared.upload_storage import MAX_UPLOAD_BYTES


client = TestClient(app)

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 32
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
WEBP_BYTES = b"RIFF" + b"\x10\x00\x00\x00" + b"WEBP" + b"\x00" * 32


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


def booking_update_file_names() -> set[str]:
    upload_dir = get_settings().upload_root_path / "booking-updates"
    if not upload_dir.exists():
        return set()
    return {item.name for item in upload_dir.iterdir() if item.is_file()}


def string_image_file_names() -> set[str]:
    upload_dir = get_settings().upload_root_path / "string-images"
    if not upload_dir.exists():
        return set()
    return {item.name for item in upload_dir.iterdir() if item.is_file()}


def enable_password_reset_preview(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)


def parse_signed_media_url(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    exp = query.get("exp", [""])[0]
    sig = query.get("sig", [""])[0]
    return parsed.path, exp, sig


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
        "/api/recommendations/generate",
        headers=headers(customer_token),
        json={"top_n": 3},
    )
    assert recommendation_response.status_code == 200
    assert recommendation_response.json()["algorithm_version"] == ALGORITHM_VERSION
    assert len(recommendation_response.json()["results"]) == 3
    top_recommendation = recommendation_response.json()["results"][0]
    assert top_recommendation["catalog_id"]
    assert (
        top_recommendation["score_breakdown"]["final_score"]
        == top_recommendation["score"]
    )
    assert set(top_recommendation["score_breakdown"]) >= {
        "preference_match",
        "rule_fit",
        "budget_fit",
        "final_score",
    }
    assert top_recommendation["rationale_payload"]["feature_sources"]

    cached_response = client.get(
        "/api/recommendations/me",
        headers=headers(customer_token),
    )
    assert cached_response.status_code == 200
    assert (
        cached_response.json()["results"][0]["catalog_id"]
        == top_recommendation["catalog_id"]
    )

    detail_response = client.get(
        f"/api/recommendations/me/{top_recommendation['catalog_id']}",
        headers=headers(customer_token),
    )
    assert detail_response.status_code == 200
    assert (
        detail_response.json()["result"]["catalog_id"]
        == top_recommendation["catalog_id"]
    )
    assert detail_response.json()["result"]["rationale_payload"]["score_breakdown"]

    with SessionLocal() as db:
        preference_rows = db.execute(select(UserPreferenceMatrix)).scalars().all()
        cache_rows = db.execute(select(RecommendationScoreCache)).scalars().all()
        assert {row.feature_key for row in preference_rows} >= {
            "repulsion",
            "control",
            "durability",
            "comfort",
            "sound",
        }
        assert all(row.raw_score is not None for row in preference_rows)
        assert len(cache_rows) == 3
        assert cache_rows[0].preference_match_score is not None
        assert cache_rows[0].budget_fit_score is not None

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
            "pricing_mode": "fixed_price",
            "stock_level": 3,
            "availability_status": "low_stock",
            "admin_note": "Reserve 2 packs for walk-in customers.",
        },
    )
    assert low_stock_response.status_code == 200
    assert low_stock_response.json()["price_rm"] == 48
    assert low_stock_response.json()["stock_level"] == 3
    assert low_stock_response.json()["availability"] == "low_stock"
    assert low_stock_response.json()["pricing_mode"] == "fixed_price"
    assert low_stock_response.json()["availability_status"] == "low_stock"
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


def test_public_string_filters_expose_normalized_catalog_fields():
    customer_token = register_customer(phone_number="+60127775555")

    all_strings = client.get("/api/strings", headers=headers(customer_token))
    assert all_strings.status_code == 200
    assert all_strings.json()["total"] >= 30

    hybrid_strings = client.get(
        "/api/strings",
        headers=headers(customer_token),
        params={"is_hybrid": True},
    )
    assert hybrid_strings.status_code == 200
    assert hybrid_strings.json()["total"] >= 1
    assert all(item["is_hybrid"] is True for item in hybrid_strings.json()["items"])

    yonex_strings = client.get(
        "/api/strings",
        headers=headers(customer_token),
        params={"brand": "Yonex"},
    )
    assert yonex_strings.status_code == 200
    assert yonex_strings.json()["total"] >= 1
    assert all(
        "Yonex" in item["display_name"] for item in yonex_strings.json()["items"]
    )

    narrow_gauge = client.get(
        "/api/strings",
        headers=headers(customer_token),
        params={"gauge_max": 0.63},
    )
    assert narrow_gauge.status_code == 200
    assert narrow_gauge.json()["total"] >= 1
    assert all(
        item["gauge_main_mm"] is not None and item["gauge_main_mm"] <= 0.63
        for item in narrow_gauge.json()["items"]
    )


def test_admin_can_persist_official_performance_and_inventory_history():
    customer_token = register_customer(phone_number="+60127776666")
    admin_token = login_admin()
    string_id = first_string_id(customer_token)

    official_before = client.get(
        f"/api/admin/strings/{string_id}/official-performance",
        headers=headers(admin_token),
    )
    assert official_before.status_code == 200
    assert official_before.json()["status"] == "pending_manual_fill"

    official_update = client.put(
        f"/api/admin/strings/{string_id}/official-performance",
        headers=headers(admin_token),
        json={
            "source_type": "manual",
            "source_name": "Yonex JP catalog",
            "repulsion_power": 9.2,
            "control": 8.4,
            "status": "manually_curated",
            "notes": "Initial official values entered by admin.",
        },
    )
    assert official_update.status_code == 200
    assert official_update.json()["source_name"] == "Yonex JP catalog"
    assert official_update.json()["repulsion_power"] == 9.2
    assert official_update.json()["status"] == "manually_curated"

    inventory_update = client.patch(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
        json={
            "current_stock": 12,
            "reserved_stock": 2,
            "selling_price": 52,
            "pricing_mode": "fixed_price",
            "availability_status": "in_stock",
            "movement_type": "RESTOCK",
            "reference_type": "manual_restock",
            "reference_id": "PO-2026-04-12",
            "admin_note": "Restocked for weekend bookings.",
        },
    )
    assert inventory_update.status_code == 200
    assert inventory_update.json()["current_stock"] == 12
    assert inventory_update.json()["reserved_stock"] == 2
    assert inventory_update.json()["available_stock"] == 10
    assert inventory_update.json()["price_rm"] == 52
    assert inventory_update.json()["pricing_mode"] == "fixed_price"
    assert inventory_update.json()["availability_status"] == "in_stock"

    movement_history = client.get(
        f"/api/admin/inventory/strings/{string_id}/movements",
        headers=headers(admin_token),
    )
    assert movement_history.status_code == 200
    assert movement_history.json()["total"] >= 1
    assert movement_history.json()["items"][0]["movement_type"] == "RESTOCK"
    assert movement_history.json()["items"][0]["reference_id"] == "PO-2026-04-12"


def test_admin_can_persist_catalog_editor_fields_and_string_image():
    customer_token = register_customer(phone_number="+60127776777")
    admin_token = login_admin()
    string_id = first_string_id(customer_token)

    before_upload = string_image_file_names()
    image_upload = client.post(
        f"/api/admin/strings/{string_id}/image",
        headers=headers(admin_token),
        files={"photo": ("string-pack.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert image_upload.status_code == 200
    image_upload_path, image_upload_exp, image_upload_sig = parse_signed_media_url(
        image_upload.json()["image_url"]
    )
    assert image_upload_path.startswith("/api/media/string-images/")
    assert image_upload_exp.isdigit()
    assert len(image_upload_sig) == 64
    after_upload = string_image_file_names()
    assert len(after_upload) == len(before_upload) + 1

    update_string = client.put(
        f"/api/admin/strings/{string_id}",
        headers=headers(admin_token),
        json={
            "brand": image_upload.json()["brand"],
            "model_name": image_upload.json()["model_name"],
            "gauge_main_mm": 0.69,
            "gauge_cross_mm": 0.69,
            "gauge_label": "0.69 mm",
            "category": "durable",
            "main_trait": "Durable",
            "tension_min_lbs": 24,
            "tension_max_lbs": 29,
            "material_summary_en": "Braided nylon multifilament",
            "full_description": "Updated from the admin editor.",
            "short_description": "Updated admin summary.",
            "original_name": "耐打测试线",
            "is_active": True,
        },
    )
    assert update_string.status_code == 200
    assert update_string.json()["category"] == "durable"
    assert update_string.json()["main_trait"] == "Durable"
    assert update_string.json()["tension_min_lbs"] == 24
    assert update_string.json()["tension_max_lbs"] == 29
    updated_image_path, _, _ = parse_signed_media_url(update_string.json()["image_url"])
    assert updated_image_path.startswith("/api/media/string-images/")

    detail_response = client.get(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["category"] == "durable"
    assert detail_response.json()["main_trait"] == "Durable"
    assert detail_response.json()["tension_min_lbs"] == 24
    assert detail_response.json()["tension_max_lbs"] == 29
    detail_image_path, _, _ = parse_signed_media_url(detail_response.json()["image_url"])
    assert detail_image_path.startswith("/api/media/string-images/")

    delete_image = client.delete(
        f"/api/admin/strings/{string_id}/image",
        headers=headers(admin_token),
    )
    assert delete_image.status_code == 200
    assert delete_image.json()["image_url"] is None
    assert len(string_image_file_names()) == len(before_upload)


def test_admin_delete_string_image_does_not_follow_parent_path_segments():
    customer_token = register_customer(phone_number="+60127776778")
    admin_token = login_admin()
    string_id = first_string_id(customer_token)

    detail_response = client.get(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
    )
    assert detail_response.status_code == 200

    update_response = client.put(
        f"/api/admin/strings/{string_id}",
        headers=headers(admin_token),
        json={
            "brand": detail_response.json()["brand"],
            "model_name": detail_response.json()["model_name"],
            "image_url": "../stringsense-path-traversal-guard.txt",
        },
    )
    assert update_response.status_code == 200

    outside_file = (
        get_settings().upload_root_path.parent / "stringsense-path-traversal-guard.txt"
    )
    outside_file.write_text("must-stay", encoding="utf-8")
    try:
        delete_response = client.delete(
            f"/api/admin/strings/{string_id}/image",
            headers=headers(admin_token),
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["image_url"] is None
        assert outside_file.exists()
    finally:
        outside_file.unlink(missing_ok=True)


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
    assert settings_response.json()["trending_string_ids"] == []
    featured_string_id = first_string_id(admin_token)

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
            "trending_string_ids": [featured_string_id],
        },
    )
    assert update_settings_response.status_code == 200
    assert update_settings_response.json()["store_name"] == "Apex String Lab Express"
    assert update_settings_response.json()["trending_string_ids"] == [featured_string_id]


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

    live_reference = f"LIVE-{booking_id[:8].upper()}"
    live_lookup_response = client.get(
        f"/api/admin/check-in/lookup?reference={live_reference}",
        headers=headers(admin_token),
    )
    assert live_lookup_response.status_code == 200
    assert live_lookup_response.json()["matched_by"] == "check_in_reference"
    assert live_lookup_response.json()["booking"]["id"] == booking_id

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


def test_admin_check_in_lookup_rejects_partial_and_wildcard_references():
    customer_token = register_customer(phone_number="+60126661112")
    admin_token = login_admin()

    create_booking_response = client.post(
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
    assert create_booking_response.status_code == 200

    wildcard_lookup = client.get(
        "/api/admin/check-in/lookup?reference=CHK-%",
        headers=headers(admin_token),
    )
    assert wildcard_lookup.status_code == 404

    partial_lookup = client.get(
        "/api/admin/check-in/lookup?reference=ORD-A",
        headers=headers(admin_token),
    )
    assert partial_lookup.status_code == 404


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
        files={"photo": ("player-racket.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert player_update.status_code == 200
    assert player_update.json()["updates"][0]["author_role"] == "customer"
    player_photo_path, player_photo_exp, player_photo_sig = parse_signed_media_url(
        player_update.json()["updates"][0]["photo_url"]
    )
    assert player_photo_path.startswith("/api/media/booking-updates/")
    assert player_photo_exp.isdigit()
    assert len(player_photo_sig) == 64
    assert player_update.json()["updates"][0]["photo_type"] == "racket"

    admin_token = login_admin()
    admin_update = client.post(
        f"/api/admin/bookings/{booking_id}/updates",
        headers=headers(admin_token),
        data={
            "comment": "Admin received the racket photo.",
            "photo_type": "service_progress",
        },
        files={"photo": ("admin-racket.png", PNG_BYTES, "image/png")},
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
        files={"photo": ("collection.webp", WEBP_BYTES, "image/webp")},
    )
    assert admin_photo_update.status_code == 200
    updates = admin_photo_update.json()["updates"]
    assert updates[-1]["author_role"] == "admin"
    assert updates[-1]["comment"] == "Reference photo before collection."
    assert updates[-1]["photo_type"] == "other"
    admin_photo_path, admin_photo_exp, admin_photo_sig = parse_signed_media_url(
        updates[-1]["photo_url"]
    )
    assert admin_photo_path.startswith("/api/media/booking-updates/")
    assert admin_photo_exp.isdigit()
    assert len(admin_photo_sig) == 64

    player_detail = client.get(
        f"/api/bookings/{booking_id}",
        headers=headers(customer_token),
    )
    assert player_detail.status_code == 200
    assert len(player_detail.json()["updates"]) == 3


def test_signed_media_endpoint_requires_valid_signature():
    customer_token = register_customer(
        username="signed-media-user",
        phone_number="+60125550129",
    )
    string_id = first_string_id(customer_token)
    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Nanoflare 800",
            "requested_tension": 25,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    update_response = client.post(
        f"/api/bookings/{booking_id}/updates",
        headers=headers(customer_token),
        files={"photo": ("signed.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert update_response.status_code == 200
    signed_url = update_response.json()["updates"][0]["photo_url"]

    ok_response = client.get(signed_url)
    assert ok_response.status_code == 200

    path, exp, _ = parse_signed_media_url(signed_url)
    invalid_sig_response = client.get(f"{path}?exp={exp}&sig={'0' * 64}")
    assert invalid_sig_response.status_code == 404

    expired_exp = 1
    relative_path = unquote(path.removeprefix("/api/media/"))
    payload = f"{relative_path}:{expired_exp}".encode("utf-8")
    secret = (get_settings().jwt_secret_key or "").encode("utf-8")
    expired_sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    expired_sig_response = client.get(f"{path}?exp={expired_exp}&sig={expired_sig}")
    assert expired_sig_response.status_code == 404


def test_admin_bookings_reject_invalid_sort_field():
    admin_token = login_admin()
    response = client.get(
        "/api/admin/bookings?sort_by=unknown_field",
        headers=headers(admin_token),
    )
    assert response.status_code == 422


def test_rejected_booking_update_photo_does_not_leave_file():
    owner_token = register_customer(
        username="photo-owner",
        phone_number="+60125550124",
    )
    other_token = register_customer(
        username="photo-other",
        phone_number="+60125550125",
    )
    string_id = first_string_id(owner_token)
    booking_response = client.post(
        "/api/bookings",
        headers=headers(owner_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Arcsaber 11",
            "requested_tension": 24,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    before_files = booking_update_file_names()
    forbidden_update = client.post(
        f"/api/bookings/{booking_id}/updates",
        headers=headers(other_token),
        data={"comment": "Trying to upload to another booking."},
        files={"photo": ("forbidden.jpg", b"forbidden-photo", "image/jpeg")},
    )
    assert forbidden_update.status_code == 404
    assert booking_update_file_names() == before_files

    missing_admin_update = client.post(
        "/api/admin/bookings/not-a-booking/photos",
        headers=headers(login_admin()),
        data={"comment": "Invalid booking upload."},
        files={"photo": ("missing.png", b"missing-photo", "image/png")},
    )
    assert missing_admin_update.status_code == 404
    assert booking_update_file_names() == before_files


def test_player_booking_update_rejects_oversized_photo_upload():
    customer_token = register_customer(
        username="oversized-photo-user",
        phone_number="+60125550126",
    )
    string_id = first_string_id(customer_token)
    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Arcsaber 7",
            "requested_tension": 24,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    before_files = booking_update_file_names()
    oversized_upload = client.post(
        f"/api/bookings/{booking_id}/updates",
        headers=headers(customer_token),
        data={"comment": "Oversized upload should be rejected."},
        files={
            "photo": (
                "too-large.jpg",
                b"x" * (MAX_UPLOAD_BYTES + 1),
                "image/jpeg",
            )
        },
    )
    assert oversized_upload.status_code == 400
    assert oversized_upload.json()["error"]["message"] == (
        "Uploaded photo must be 5 MB or smaller"
    )
    assert booking_update_file_names() == before_files


def test_player_booking_update_rejects_mime_spoofed_photo_upload():
    customer_token = register_customer(
        username="spoofed-photo-user",
        phone_number="+60125550130",
    )
    string_id = first_string_id(customer_token)
    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Arcsaber 7",
            "requested_tension": 24,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    before_files = booking_update_file_names()
    spoofed_upload = client.post(
        f"/api/bookings/{booking_id}/updates",
        headers=headers(customer_token),
        files={"photo": ("spoofed.jpg", PNG_BYTES, "image/jpeg")},
    )
    assert spoofed_upload.status_code == 400
    assert spoofed_upload.json()["error"]["message"] == (
        "Uploaded photo must be a valid JPG, PNG, or WEBP image"
    )
    assert booking_update_file_names() == before_files


def test_admin_booking_photo_upload_rejects_oversized_photo_upload():
    customer_token = register_customer(
        username="oversized-admin-photo-user",
        phone_number="+60125550127",
    )
    string_id = first_string_id(customer_token)
    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Astrox 88D",
            "requested_tension": 25,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    before_files = booking_update_file_names()
    oversized_upload = client.post(
        f"/api/admin/bookings/{booking_id}/photos",
        headers=headers(login_admin()),
        data={"comment": "Oversized photo should be rejected."},
        files={
            "photo": (
                "too-large-admin.jpg",
                b"x" * (MAX_UPLOAD_BYTES + 1),
                "image/jpeg",
            )
        },
    )
    assert oversized_upload.status_code == 400
    assert oversized_upload.json()["error"]["message"] == (
        "Uploaded photo must be 5 MB or smaller"
    )
    assert booking_update_file_names() == before_files


def test_admin_string_image_upload_rejects_oversized_image_upload():
    customer_token = register_customer(phone_number="+60125550128")
    string_id = first_string_id(customer_token)
    before_files = string_image_file_names()

    oversized_upload = client.post(
        f"/api/admin/strings/{string_id}/image",
        headers=headers(login_admin()),
        files={
            "photo": (
                "too-large-image.png",
                b"x" * (MAX_UPLOAD_BYTES + 1),
                "image/png",
            )
        },
    )
    assert oversized_upload.status_code == 400
    assert oversized_upload.json()["error"]["message"] == (
        "Uploaded image must be 5 MB or smaller"
    )
    assert string_image_file_names() == before_files
