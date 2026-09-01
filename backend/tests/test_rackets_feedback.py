from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_recommendation_repository import (
    SqlAlchemyRecommendationRepository,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.domain.recommendation.scoring import ALGORITHM_VERSION
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


def test_standard_racket_catalog_and_server_owned_identity() -> None:
    token = register_customer(
        username="racket-catalog-owner",
        phone_number="+60121110020",
    )

    assert client.get("/api/racket-models").status_code == 401
    catalog_response = client.get("/api/racket-models", headers=headers(token))
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert len(catalog) == 6
    assert len({item["key"] for item in catalog}) == len(catalog)

    model_key = "yonex:astrox 88d pro"
    standard_response = client.post(
        "/api/rackets",
        headers=headers(token),
        json={
            "nickname": "Server canonical frame",
            "model_key": model_key,
            "brand": "Spoofed brand",
            "model": "Spoofed model",
        },
    )
    assert standard_response.status_code == 200
    standard = standard_response.json()
    assert standard["model_key"] == model_key
    assert standard["brand"] == "Yonex"
    assert standard["model"] == "Astrox 88D Pro"

    with SessionLocal() as db:
        db.add(
            RecommendationScoreCache(
                user_id=str(standard["user_id"]),
                catalog_id=first_string_id(token),
                algorithm_version=ALGORITHM_VERSION,
                final_score=0.9,
                rank_position=1,
                rationale={},
            )
        )
        db.commit()
    changed_model = client.patch(
        f"/api/rackets/{standard['id']}",
        headers=headers(token),
        json={"model_key": "yonex:arcsaber 11 pro"},
    )
    assert changed_model.status_code == 200
    assert changed_model.json()["model"] == "Arcsaber 11 Pro"
    with SessionLocal() as db:
        assert db.execute(select(RecommendationScoreCache)).scalar_one_or_none() is None

    unknown_response = client.post(
        "/api/rackets",
        headers=headers(token),
        json={
            "nickname": "Unknown key",
            "model_key": "yonex:not-a-real-model",
            "brand": "Yonex",
            "model": "Not a real model",
        },
    )
    assert unknown_response.status_code == 400

    custom_response = client.post(
        "/api/rackets",
        headers=headers(token),
        json={
            "nickname": "Custom frame",
            "model_key": None,
            "brand": "Apacs",
            "model": "Z-Ziggler",
        },
    )
    assert custom_response.status_code == 200
    custom = custom_response.json()
    assert custom["model_key"] is None

    with SessionLocal() as db:
        context = SqlAlchemyRecommendationRepository(db).get_owned_racket_context(
            user_id=str(custom["user_id"]),
            racket_id=str(custom["id"]),
            target_tension=26,
        )
    assert context is not None
    assert context.model_key is None


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
    assert racket["model_key"] == "yonex:astrox 88d pro"

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

    list_after_completion = client.get(
        "/api/rackets",
        headers=headers(owner_token),
    )
    assert list_after_completion.status_code == 200
    summary = next(
        item for item in list_after_completion.json() if item["id"] == racket_id
    )
    assert summary["service_count"] == 1
    assert summary["current_string_id"] == completed_booking["string_id"]
    assert summary["current_tension"] == 27
    assert summary["last_serviced_at"] is not None


def test_structured_feedback_patch_without_durability_or_provenance() -> None:
    owner_token = register_customer(
        username="feedback-structured",
        phone_number="+60121110013",
    )
    other_token = register_customer(
        username="feedback-structured-other",
        phone_number="+60121110014",
    )
    booking = create_booking(owner_token, str(create_racket(owner_token)["id"]))
    booking_id = str(booking["id"])
    complete_booking(login_admin(), booking_id)

    created = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={"rating": 4, "control": 4},
    )
    assert created.status_code == 200
    assert created.json()["comment"] is None
    assert "durability" not in created.json()
    assert "structured_field_confirmed_at" not in created.json()

    player_summary = client.get(
        "/api/strings/feedback-summary",
        headers=headers(owner_token),
    )
    assert player_summary.status_code == 200
    assert (
        client.get(
            "/api/strings/community-summary",
            headers=headers(owner_token),
        ).status_code
        == 404
    )
    summary_string = next(
        item
        for item in player_summary.json()["strings"]
        if item["string_id"] == booking["string_id"]
    )
    assert summary_string["features"]["control"]["distinct_users"] == 1

    admin_summary = client.get(
        "/api/admin/feedback/summary",
        headers=headers(login_admin()),
    )
    assert admin_summary.status_code == 200
    assert admin_summary.json()["racket_contexts"]
    assert (
        client.get(
            "/api/admin/feedback/community-summary",
            headers=headers(login_admin()),
        ).status_code
        == 404
    )

    forbidden = client.patch(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(other_token),
        json={"control": 1},
    )
    assert forbidden.status_code == 404
    assert (
        client.patch(
            f"/api/bookings/{booking_id}/feedback",
            headers=headers(owner_token),
            json={},
        ).status_code
        == 422
    )

    text_only = client.patch(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={"string_feedback": "Still crisp."},
    )
    assert text_only.status_code == 200

    removed_durability = client.patch(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={"durability": 4},
    )
    assert removed_durability.status_code == 422


def test_personal_feedback_clears_the_owner_recommendation_cache() -> None:
    owner_token = register_customer(
        username="feedback-cache-owner",
        phone_number="+60121110015",
    )
    racket = create_racket(owner_token)
    booking = create_booking(owner_token, str(racket["id"]))
    booking_id = str(booking["id"])
    complete_booking(login_admin(), booking_id)

    with SessionLocal() as db:
        db.add(
            RecommendationScoreCache(
                user_id=str(booking["user_id"]),
                catalog_id=str(booking["string_id"]),
                algorithm_version=ALGORITHM_VERSION,
                final_score=0.5,
                rank_position=1,
                rationale={},
            )
        )
        db.commit()

    with SessionLocal() as db:
        assert (
            db.execute(
                select(RecommendationScoreCache).where(
                    RecommendationScoreCache.user_id == str(booking["user_id"]),
                    RecommendationScoreCache.algorithm_version == ALGORITHM_VERSION,
                )
            )
            .scalars()
            .first()
            is not None
        )

    response = client.post(
        f"/api/bookings/{booking_id}/feedback",
        headers=headers(owner_token),
        json={
            "rating": 4,
            "string_satisfaction": 5,
            "would_use_again": False,
        },
    )
    assert response.status_code == 200

    with SessionLocal() as db:
        assert (
            db.execute(
                select(RecommendationScoreCache).where(
                    RecommendationScoreCache.user_id == str(booking["user_id"]),
                    RecommendationScoreCache.algorithm_version == ALGORITHM_VERSION,
                )
            )
            .scalars()
            .first()
            is None
        )
