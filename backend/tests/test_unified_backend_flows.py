from __future__ import annotations

from datetime import date
from datetime import timedelta

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import UserPreferenceMatrix
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.entrypoints.api.routes import auth_routes
from app.main import app
from app.shared.upload_storage import MAX_UPLOAD_BYTES


client = TestClient(app)

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 32
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
WEBP_BYTES = b"RIFF" + b"\x10\x00\x00\x00" + b"WEBP" + b"\x00" * 32


def next_weekday(weekday: int) -> date:
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7 or 7
    return today + timedelta(days=days_ahead)


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


def first_admin_string_id(token: str) -> str:
    response = client.get("/api/admin/inventory/strings", headers=headers(token))
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


def test_health_aliases_share_the_same_contract():
    root_response = client.get("/health")
    api_response = client.get("/api/health")

    assert root_response.status_code == 200
    assert api_response.status_code == 200
    assert api_response.json() == root_response.json()
    assert root_response.json()["recommendation_artifact"]["rows"] == 108


def test_auth_profile_booking_and_admin_status_flow():
    customer_token = register_customer()

    me_response = client.get("/api/auth/me", headers=headers(customer_token))
    assert me_response.status_code == 200
    assert me_response.json()["phone_number"] == "+60123456789"

    empty_profile_response = client.get(
        "/api/profile",
        headers=headers(customer_token),
    )
    assert empty_profile_response.status_code == 200
    assert empty_profile_response.json() is None

    upsert_profile_response = client.put(
        "/api/profile",
        headers=headers(customer_token),
        json={
            "username": "Tan Wei Jie Updated",
            "skill_level": "intermediate",
            "playing_style": "attacking",
            "preferred_tension": 25,
            "frequency_per_week": 3,
            "preferred_feel": "medium",
            "preferred_gauge": "no_preference",
            "recent_goal": "power",
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
    assert upsert_profile_response.json()["username"] == "Tan Wei Jie Updated"
    assert upsert_profile_response.json()["playing_style"] == "attacking"

    updated_me_response = client.get(
        "/api/auth/me",
        headers=headers(customer_token),
    )
    assert updated_me_response.status_code == 200
    assert updated_me_response.json()["username"] == "Tan Wei Jie Updated"

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
        json={
            "status": "in_progress",
            "expected_completion_datetime": "2026-04-23T18:30:00Z",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"
    assert update_response.json()["order_code"] == order_code
    assert update_response.json()["expected_completion_datetime"].startswith(
        "2026-04-23T18:30:00"
    )
    assert len(update_response.json()["status_history"]) == 2

    eta_only_response = client.patch(
        f"/api/admin/bookings/{booking_id}/status",
        headers=headers(admin_token),
        json={
            "status": "in_progress",
            "expected_completion_datetime": "2026-04-24T09:15:00Z",
        },
    )
    assert eta_only_response.status_code == 200
    assert eta_only_response.json()["status"] == "in_progress"
    assert eta_only_response.json()["expected_completion_datetime"].startswith(
        "2026-04-24T09:15:00"
    )
    assert len(eta_only_response.json()["status_history"]) == 2


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
            "preferred_tension": 26,
            "frequency_per_week": 4,
            "preferred_feel": "medium",
            "preferred_gauge": "thick",
            "recent_goal": "balanced",
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

    racket_response = client.post(
        "/api/rackets",
        headers=headers(customer_token),
        json={
            "nickname": "Recommendation racket",
            "brand": "Yonex",
            "model": "Astrox 88D Pro",
        },
    )
    assert racket_response.status_code == 200
    racket_id = racket_response.json()["id"]

    recommendation_response = client.post(
        "/api/recommendations/generate",
        headers=headers(customer_token),
        json={"top_n": 3, "racket_id": racket_id},
    )
    assert recommendation_response.status_code == 200
    assert recommendation_response.json()["algorithm_version"] == ALGORITHM_VERSION
    assert recommendation_response.json()["run_id"]
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
        "value_for_money",
        "final_score",
    }
    rationale = top_recommendation["rationale_payload"]
    assert rationale["racket_context"]["racket_id"] == racket_id
    assert rationale["racket_context"]["normalized_model_key"] == (
        "yonex:astrox 88d pro"
    )
    assert rationale["collaborative_filtering_used"] is False
    assert rationale["cf_shadow"]["cf_weight"] == 0
    assert rationale["community_snapshot_version"].startswith("sha256:")
    assert rationale["feature_sources"]
    assert all(
        not {
            "confidence_score",
            "source_ref",
            "source_version",
            "source_generated_at",
            "review_count_snapshot",
        }.intersection(row)
        for row in rationale["feature_evidence"]
    )

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
    assert detail_response.json()["run_id"] == recommendation_response.json()["run_id"]

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
        assert cache_rows[0].value_for_money_score is not None

    log_response = client.get(
        "/api/admin/recommendations/logs",
        headers=headers(admin_token),
    )
    assert log_response.status_code == 200
    assert log_response.json()["total"] == 1
    assert log_response.json()["items"][0]["phone_number"] == "+60128888888"

    runs_response = client.get(
        "/api/admin/recommendations/runs",
        headers=headers(admin_token),
    )
    assert runs_response.status_code == 200
    assert runs_response.json()["total"] == 1
    run = runs_response.json()["items"][0]
    assert len(run["items"]) == 3
    assert "confidence_score" not in run["items"][0]

    run_detail_response = client.get(
        f"/api/admin/recommendations/runs/{run['id']}",
        headers=headers(admin_token),
    )
    assert run_detail_response.status_code == 200
    assert run_detail_response.json()["id"] == run["id"]
    assert len(run_detail_response.json()["items"]) == 3

    removed_duplicate_route = client.get(
        "/api/recommendations/logs",
        headers=headers(admin_token),
    )
    assert removed_duplicate_route.status_code == 403

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
    assert out_of_stock_response.json()["is_active"] is True

    public_lookup = client.get(
        f"/api/strings/{string_id}",
        headers=headers(customer_token),
    )
    assert public_lookup.status_code == 404


def test_public_string_filters_expose_normalized_catalog_fields():
    customer_token = register_customer(phone_number="+60127775555")

    all_strings = client.get("/api/strings", headers=headers(customer_token))
    assert all_strings.status_code == 200
    assert all_strings.json()["total"] == 12

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

    inventory_before = client.get(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
    )
    assert inventory_before.status_code == 200
    previous_available_stock = inventory_before.json()["available_stock"]

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
    assert (
        movement_history.json()["items"][0]["quantity"] == 10 - previous_available_stock
    )


def test_admin_string_editor_updates_all_sections_atomically():
    customer_token = register_customer(phone_number="+60127776667")
    admin_token = login_admin()
    string_id = first_string_id(customer_token)

    detail_before = client.get(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
    )
    assert detail_before.status_code == 200
    before = detail_before.json()

    update_response = client.put(
        f"/api/admin/inventory/strings/{string_id}/editor",
        headers=headers(admin_token),
        json={
            "catalog": {
                "brand": before["brand"],
                "model_name": before["model_name"],
                "is_hybrid": before["is_hybrid"],
                "gauge_main_mm": before["gauge_main_mm"],
                "gauge_cross_mm": before["gauge_cross_mm"],
                "short_description": "Saved through the atomic editor.",
            },
            "inventory": {
                "current_stock": before["current_stock"] + 4,
                "reserved_stock": before["reserved_stock"],
                "selling_price": 56,
                "pricing_mode": "fixed_price",
                "movement_type": "RESTOCK",
                "admin_note": "Atomic editor restock.",
            },
            "official_performance": {
                "source_type": "manual",
                "source_name": "Atomic editor source",
                "control": 8.8,
                "status": "manually_curated",
            },
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["short_description"] == "Saved through the atomic editor."
    assert updated["current_stock"] == before["current_stock"] + 4
    assert updated["available_stock"] == before["available_stock"] + 4
    assert updated["selling_price"] == 56
    assert updated["official_performance_status"] == "manually_curated"

    official_response = client.get(
        f"/api/admin/strings/{string_id}/official-performance",
        headers=headers(admin_token),
    )
    assert official_response.status_code == 200
    assert official_response.json()["source_name"] == "Atomic editor source"
    assert official_response.json()["control"] == 8.8

    movement_history = client.get(
        f"/api/admin/inventory/strings/{string_id}/movements",
        headers=headers(admin_token),
    )
    assert movement_history.status_code == 200
    assert movement_history.json()["items"][0]["quantity"] == 4


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
    assert image_upload.json()["image_url"].startswith("/api/media/string-images/")
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
    assert update_string.json()["image_url"].startswith("/api/media/string-images/")

    detail_response = client.get(
        f"/api/admin/inventory/strings/{string_id}",
        headers=headers(admin_token),
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["category"] == "durable"
    assert detail_response.json()["main_trait"] == "Durable"
    assert detail_response.json()["tension_min_lbs"] == 24
    assert detail_response.json()["tension_max_lbs"] == 29
    assert detail_response.json()["image_url"].startswith("/api/media/string-images/")

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
    slot_date = next_weekday(0)

    hours_response = client.get(
        "/api/admin/business-hours",
        headers=headers(admin_token),
    )
    assert hours_response.status_code == 200
    assert len(hours_response.json()["days"]) == 7
    assert hours_response.json()["special_closed_dates"] == []

    slots_before_booking = client.get(
        f"/api/slots?date={slot_date.isoformat()}",
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
            "drop_off_datetime": f"{slot_date.isoformat()}T11:00:00",
        },
    )
    assert booking_response.status_code == 200

    slots_after_booking = client.get(
        f"/api/admin/slots?date={slot_date.isoformat()}",
        headers=headers(admin_token),
    )
    assert slots_after_booking.status_code == 200
    updated_slot = next(
        item for item in slots_after_booking.json()["items"] if item["time"] == "11:00"
    )
    assert updated_slot["available_spots"] == updated_slot["capacity"] - 1

    updated_hours_payload = hours_response.json()
    updated_hours_payload["special_closed_dates"] = [slot_date.isoformat()]
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
        f"/api/admin/slots?date={slot_date.isoformat()}",
        headers=headers(admin_token),
    )
    assert closed_slots_response.status_code == 200
    assert closed_slots_response.json()["items"] == []

    settings_response = client.get(
        "/api/admin/store-settings",
        headers=headers(admin_token),
    )
    assert settings_response.status_code == 200
    assert settings_response.json()["store_name"] == "StringSence"
    assert settings_response.json()["trending_string_ids"] == []
    featured_string_id = first_admin_string_id(admin_token)

    update_settings_response = client.put(
        "/api/admin/store-settings",
        headers=headers(admin_token),
        json={
            "store_name": "StringSence Test Branch",
            "store_contact": "+60 12-111 2222",
            "support_text": "Admin desk handles booking and string setup support.",
            "payment_notes": "External payments require shop verification.",
            "booking_notes": "Slots are capped by configured store capacity.",
            "store_policy_text": "Completed bookings are final after collection.",
            "address": "Utar Kampar Test Counter",
            "trending_string_ids": [featured_string_id],
        },
    )
    assert update_settings_response.status_code == 200
    assert update_settings_response.json()["store_name"] == "StringSence Test Branch"
    assert update_settings_response.json()["trending_string_ids"] == [
        featured_string_id
    ]

    public_settings_response = client.get(
        "/api/store-settings",
        headers=headers(customer_token),
    )
    assert public_settings_response.status_code == 200
    assert public_settings_response.json()["trending_string_ids"] == [
        featured_string_id
    ]


def test_booking_slot_id_rejects_past_closed_off_grid_and_full_slots():
    customer_token = register_customer(phone_number="+60125554445")
    admin_token = login_admin()
    string_id = first_string_id(customer_token)
    slot_date = next_weekday(0)
    slot_response = client.get(
        f"/api/slots?date={slot_date.isoformat()}",
        headers=headers(customer_token),
    )
    assert slot_response.status_code == 200
    selected_slot = next(
        item for item in slot_response.json()["items"] if item["time"] == "11:00"
    )

    payload = {
        "string_id": string_id,
        "racket_brand": "Yonex",
        "racket_model": "Astrox 88D",
        "requested_tension": 25,
        "slot_id": selected_slot["id"],
    }
    created_responses = [
        client.post("/api/bookings", headers=headers(customer_token), json=payload)
        for _ in range(selected_slot["capacity"])
    ]
    assert all(response.status_code == 200 for response in created_responses)
    assert all(
        response.json()["slot_id"] == selected_slot["id"]
        for response in created_responses
    )

    full_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json=payload,
    )
    assert full_response.status_code == 409
    assert full_response.json()["error"]["message"] == ("Drop-off slot is fully booked")

    past_date = date.today() - timedelta(days=1)
    past_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={**payload, "slot_id": f"slot-{past_date.isoformat()}-11:00"},
    )
    assert past_response.status_code == 400
    assert past_response.json()["error"]["message"] == (
        "Drop-off slot must be in the future"
    )

    off_grid_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={**payload, "slot_id": f"slot-{slot_date.isoformat()}-11:15"},
    )
    assert off_grid_response.status_code == 400
    assert off_grid_response.json()["error"]["message"] == (
        "Drop-off slot is not offered by the store"
    )

    hours_response = client.get(
        "/api/admin/business-hours",
        headers=headers(admin_token),
    )
    hours_payload = hours_response.json()
    close_response = client.put(
        "/api/admin/business-hours",
        headers=headers(admin_token),
        json={
            "days": hours_payload["days"],
            "special_closed_dates": [slot_date.isoformat()],
        },
    )
    assert close_response.status_code == 200
    closed_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={**payload, "slot_id": f"slot-{slot_date.isoformat()}-12:00"},
    )
    assert closed_response.status_code == 400
    assert closed_response.json()["error"]["message"] == (
        "Drop-off slot is not offered by the store"
    )


def test_business_hours_reject_invalid_schedule_shapes():
    admin_token = login_admin()
    hours_response = client.get(
        "/api/admin/business-hours",
        headers=headers(admin_token),
    )
    assert hours_response.status_code == 200
    valid_days = hours_response.json()["days"]

    invalid_time_days = [dict(day) for day in valid_days]
    invalid_time_days[0]["open_time"] = "25:00"
    invalid_time_response = client.put(
        "/api/admin/business-hours",
        headers=headers(admin_token),
        json={"days": invalid_time_days, "special_closed_dates": []},
    )
    assert invalid_time_response.status_code == 422

    partial_break_days = [dict(day) for day in valid_days]
    partial_break_days[0]["break_end"] = None
    partial_break_response = client.put(
        "/api/admin/business-hours",
        headers=headers(admin_token),
        json={"days": partial_break_days, "special_closed_dates": []},
    )
    assert partial_break_response.status_code == 422

    missing_day_response = client.put(
        "/api/admin/business-hours",
        headers=headers(admin_token),
        json={"days": valid_days[:-1], "special_closed_dates": []},
    )
    assert missing_day_response.status_code == 422

    duplicated_close_date = next_weekday(5).isoformat()
    duplicate_close_response = client.put(
        "/api/admin/business-hours",
        headers=headers(admin_token),
        json={
            "days": valid_days,
            "special_closed_dates": [duplicated_close_date, duplicated_close_date],
        },
    )
    assert duplicate_close_response.status_code == 422


def test_admin_check_in_and_service_queue_flow():
    customer_token = register_customer(phone_number="+60126661111")
    admin_token = login_admin()
    slot_date = next_weekday(1)

    first_booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": first_string_id(customer_token),
            "racket_brand": "Victor",
            "racket_model": "Auraspeed",
            "requested_tension": 24,
            "drop_off_datetime": f"{slot_date.isoformat()}T11:00:00",
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
            "drop_off_datetime": f"{slot_date.isoformat()}T12:00:00",
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
    assert lanes["in_progress"][0]["booking"]["drop_off_datetime"].endswith("+00:00")
    assert lanes["in_progress"][0]["booking"]["slot_id"] == (
        f"slot-{slot_date.isoformat()}-11:00"
    )
    assert len(lanes["awaiting_dropoff"]) == 1
    assert lanes["awaiting_dropoff"][0]["queue_position"] == 1


def test_admin_analytics_summary_and_popular_strings():
    customer_token = register_customer(phone_number="+60127773333")
    admin_token = login_admin()
    first_slot_date = next_weekday(2)
    second_slot_date = next_weekday(3)

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
            "drop_off_datetime": f"{first_slot_date.isoformat()}T11:00:00",
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
            "drop_off_datetime": f"{first_slot_date.isoformat()}T12:00:00",
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
            "drop_off_datetime": f"{second_slot_date.isoformat()}T11:00:00",
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
    assert summary_response.json()["today_bookings"] == 0
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
    settings = get_settings()
    monkeypatch.setattr(settings, "openwa_enabled", True)
    provider_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        auth_routes,
        "send_openwa_text",
        lambda **kwargs: provider_calls.append(kwargs),
    )

    response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60127777777"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent if the account exists"
    assert response.json()["dev_code_preview"] is None
    assert provider_calls == []


def test_password_reset_code_is_committed_before_whatsapp_delivery(monkeypatch):
    enable_password_reset_preview(monkeypatch)
    register_customer()
    settings = get_settings()
    monkeypatch.setattr(settings, "openwa_enabled", True)
    monkeypatch.setattr(settings, "openwa_base_url", "http://openwa.test/api")
    monkeypatch.setattr(settings, "openwa_session_id", "session-1")
    monkeypatch.setattr(settings, "openwa_api_key", SecretStr("openwa-test-key"))
    provider_calls: list[dict[str, object]] = []

    def fake_send_openwa_text(**kwargs) -> str:
        with SessionLocal() as db:
            reset_code = db.scalar(
                select(PasswordResetCode).where(PasswordResetCode.used_at.is_(None))
            )
            assert reset_code is not None
        provider_calls.append(kwargs)
        return "wa-reset-message-1"

    monkeypatch.setattr(auth_routes, "send_openwa_text", fake_send_openwa_text)
    response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60123456789"},
    )

    assert response.status_code == 200
    verification_code = response.json()["dev_code_preview"]
    assert verification_code is not None
    assert response.json()["message"] == "Verification code sent if the account exists"
    assert provider_calls == [
        {
            "endpoint": (
                "http://openwa.test/api/sessions/session-1/messages/send-text"
            ),
            "api_key": "openwa-test-key",
            "chat_id": "60123456789@c.us",
            "text": (
                f"Your StringSense verification code is {verification_code}. "
                "It expires in 10 minutes. Do not share this code."
            ),
        }
    ]


def test_password_reset_stays_generic_when_whatsapp_delivery_fails(monkeypatch):
    enable_password_reset_preview(monkeypatch)
    register_customer()
    settings = get_settings()
    monkeypatch.setattr(settings, "openwa_enabled", True)

    def fail_send_openwa_text(**_kwargs) -> str:
        raise OSError("provider unavailable")

    monkeypatch.setattr(auth_routes, "send_openwa_text", fail_send_openwa_text)
    response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60123456789"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent if the account exists"
    assert response.json()["dev_code_preview"] is not None


def test_customer_can_reset_password_with_verification_code(monkeypatch):
    enable_password_reset_preview(monkeypatch)
    existing_token = register_customer()

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
    assert (
        client.get("/api/auth/me", headers=headers(existing_token)).status_code == 401
    )

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


def test_new_password_reset_code_replaces_the_previous_code(monkeypatch):
    enable_password_reset_preview(monkeypatch)
    register_customer()
    generated_codes = iter((111111, 222222))
    monkeypatch.setattr(
        "app.use_cases.auth.request_password_reset.secrets.randbelow",
        lambda _: next(generated_codes),
    )

    first_response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60123456789"},
    )
    second_response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": "+60123456789"},
    )
    first_code = first_response.json()["dev_code_preview"]
    second_code = second_response.json()["dev_code_preview"]
    assert first_code and second_code

    with SessionLocal() as db:
        active_codes = db.scalars(
            select(PasswordResetCode).where(PasswordResetCode.used_at.is_(None))
        ).all()
    assert len(active_codes) == 1

    replaced_response = client.post(
        "/api/auth/forgot-password/reset",
        json={
            "phone_number": "+60123456789",
            "verification_code": first_code,
            "new_password": "newpass456",
        },
    )
    active_response = client.post(
        "/api/auth/forgot-password/reset",
        json={
            "phone_number": "+60123456789",
            "verification_code": second_code,
            "new_password": "newpass456",
        },
    )
    assert replaced_response.status_code == 400
    assert active_response.status_code == 200


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
    assert missing_note_response.status_code == 409

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
    slot_date = next_weekday(6)
    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": string_id,
            "racket_brand": "Yonex",
            "racket_model": "Astrox 77",
            "requested_tension": 25,
            "drop_off_datetime": f"{slot_date.isoformat()}T10:00:00",
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
    assert player_update.json()["updates"][0]["photo_url"].startswith(
        "/api/media/booking-updates/"
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
    assert updates[-1]["photo_url"].startswith("/api/media/booking-updates/")

    player_detail = client.get(
        f"/api/bookings/{booking_id}",
        headers=headers(customer_token),
    )
    assert player_detail.status_code == 200
    assert len(player_detail.json()["updates"]) == 3


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
        files={"photo": ("forbidden.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert forbidden_update.status_code == 404
    assert booking_update_file_names() == before_files

    missing_admin_update = client.post(
        "/api/admin/bookings/not-a-booking/photos",
        headers=headers(login_admin()),
        data={"comment": "Invalid booking upload."},
        files={"photo": ("missing.png", PNG_BYTES, "image/png")},
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


def test_notification_preferences_and_verified_wallet_payment_flow():
    customer_token = register_customer(phone_number="+60125550999")
    admin_token = login_admin()

    preferences_response = client.get(
        "/api/notifications/preferences",
        headers=headers(customer_token),
    )
    assert preferences_response.status_code == 200
    assert preferences_response.json()["booking"] is True

    updated_preferences = {
        **preferences_response.json(),
        "payment": False,
    }
    update_preferences_response = client.put(
        "/api/notifications/preferences",
        headers=headers(customer_token),
        json=updated_preferences,
    )
    assert update_preferences_response.status_code == 200
    assert update_preferences_response.json()["payment"] is False

    qr_response = client.post(
        "/api/admin/store-settings/payment-qr",
        headers=headers(admin_token),
        files={"photo": ("shop-qr.png", PNG_BYTES, "image/png")},
    )
    assert qr_response.status_code == 200

    top_up_response = client.post(
        "/api/wallet/top-ups",
        headers=headers(customer_token),
        data={"amount": "500", "method": "qr_transfer"},
        files={"proof": ("payment.png", PNG_BYTES, "image/png")},
    )
    assert top_up_response.status_code == 200
    assert top_up_response.json()["status"] == "pending"
    top_up_id = top_up_response.json()["id"]

    pending_wallet = client.get("/api/wallet", headers=headers(customer_token))
    assert pending_wallet.status_code == 200
    assert pending_wallet.json()["available_balance"] == 0
    assert pending_wallet.json()["pending_top_up"] == 500

    verify_top_up_response = client.patch(
        f"/api/admin/payments/{top_up_id}",
        headers=headers(admin_token),
        json={"status": "paid"},
    )
    assert verify_top_up_response.status_code == 200
    assert verify_top_up_response.json()["status"] == "paid"

    funded_wallet = client.get("/api/wallet", headers=headers(customer_token))
    assert funded_wallet.status_code == 200
    assert funded_wallet.json()["available_balance"] == 500
    assert funded_wallet.json()["pending_top_up"] == 0
    assert len(funded_wallet.json()["transactions"]) == 1

    inventory_response = client.get(
        "/api/admin/inventory/strings",
        headers=headers(admin_token),
    )
    assert inventory_response.status_code == 200
    priced_string = next(
        item
        for item in inventory_response.json()["items"]
        if item["pricing_mode"] == "fixed_price" and item["selling_price"] > 0
    )
    booking_response = client.post(
        "/api/bookings",
        headers=headers(customer_token),
        json={
            "string_id": priced_string["id"],
            "racket_brand": "Yonex",
            "racket_model": "Astrox 99",
            "requested_tension": 26,
        },
    )
    assert booking_response.status_code == 200

    wallet_payment_response = client.post(
        f"/api/payments/bookings/{booking_response.json()['id']}",
        headers=headers(customer_token),
        data={"method": "wallet_balance"},
    )
    assert wallet_payment_response.status_code == 200
    assert wallet_payment_response.json()["status"] == "paid"

    debited_wallet = client.get("/api/wallet", headers=headers(customer_token))
    assert debited_wallet.status_code == 200
    assert debited_wallet.json()["available_balance"] < 500
    assert len(debited_wallet.json()["transactions"]) == 2
