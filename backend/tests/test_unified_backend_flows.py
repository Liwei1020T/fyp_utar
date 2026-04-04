from __future__ import annotations

from fastapi.testclient import TestClient

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
        "/api/v1/auth/register",
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
        "/api/v1/auth/login",
        json={
            "phone_number": "+60190000000",
            "password": "admin1234",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def first_string_id(token: str) -> str:
    response = client.get("/api/v1/strings", headers=headers(token))
    assert response.status_code == 200
    return response.json()["items"][0]["id"]


def test_auth_profile_booking_and_admin_status_flow():
    customer_token = register_customer()

    me_response = client.get("/api/v1/auth/me", headers=headers(customer_token))
    assert me_response.status_code == 200
    assert me_response.json()["phone_number"] == "+60123456789"

    upsert_profile_response = client.put(
        "/api/v1/profile",
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
        "/api/v1/bookings",
        headers=headers(customer_token),
        json={
            "string_id": first_string_id(customer_token),
            "racket_brand": "Yonex",
            "racket_model": "Astrox 88D",
            "requested_tension": 25,
        },
    )
    assert booking_response.status_code == 200
    assert booking_response.json()["status"] == "pending"
    booking_id = booking_response.json()["id"]

    my_bookings_response = client.get(
        "/api/v1/bookings",
        headers=headers(customer_token),
    )
    assert my_bookings_response.status_code == 200
    assert my_bookings_response.json()["total"] == 1
    assert my_bookings_response.json()["items"][0]["id"] == booking_id

    admin_token = login_admin()
    admin_list_response = client.get(
        "/api/v1/admin/bookings",
        headers=headers(admin_token),
    )
    assert admin_list_response.status_code == 200
    assert admin_list_response.json()["total"] == 1

    update_response = client.patch(
        f"/api/v1/admin/bookings/{booking_id}/status",
        headers=headers(admin_token),
        json={"status": "confirmed"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "confirmed"
    assert len(update_response.json()["status_history"]) == 2


def test_recommendations_logs_and_admin_string_controls():
    customer_token = register_customer(phone_number="+60128888888")
    admin_token = login_admin()

    profile_response = client.put(
        "/api/v1/profile",
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
        "/api/v1/recommendations/profile",
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
        "/api/v1/admin/recommendations/logs",
        headers=headers(admin_token),
    )
    assert log_response.status_code == 200
    assert log_response.json()["total"] == 1
    assert log_response.json()["items"][0]["phone_number"] == "+60128888888"

    removed_duplicate_route = client.get(
        "/api/v1/recommendations/logs",
        headers=headers(admin_token),
    )
    assert removed_duplicate_route.status_code == 404

    admin_strings = client.get(
        "/api/v1/admin/strings",
        headers=headers(admin_token),
    )
    assert admin_strings.status_code == 200
    string_item = admin_strings.json()["items"][0]

    update_string = client.put(
        f"/api/v1/admin/strings/{string_item['id']}",
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
        f"/api/v1/admin/strings/{string_item['id']}",
        headers=headers(admin_token),
    )
    assert deactivate_string.status_code == 200
    assert deactivate_string.json()["is_active"] is False
