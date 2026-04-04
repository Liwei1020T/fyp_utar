from fastapi.testclient import TestClient
import json
from pathlib import Path
from sqlalchemy import select

from app.db.models import RecommendationLog
from app.db.session import SessionLocal
from app.main import app


client = TestClient(app)


def _headers(token: str = "customer-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_function():
    from app.services.auth_service import auth_service
    from app.services.recommendation_service import recommendation_service
    from app.services.string_service import string_service

    auth_service.reset()
    recommendation_service.reset()
    string_service.reset()


def _register_customer_token() -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )
    return response.json()["data"]["access_token"]


def test_generate_recommendations_returns_ranked_results():
    customer_token = _register_customer_token()

    response = client.post(
        "/api/v1/recommendations/generate",
        json={
            "skill_level": "intermediate",
            "playing_style": "balanced",
            "budget": {"min": 30, "max": 45},
            "preferred_tension": 25,
            "durability_priority": 4,
            "repulsion_priority": 4,
            "control_priority": 5,
            "sound_priority": 3,
            "tension_retention_priority": 4,
        },
        headers=_headers(customer_token),
    )

    assert response.status_code == 200
    assert len(response.json()["data"]["results"]) >= 1
    assert "match_score" in response.json()["data"]["results"][0]
    assert "short_reason" in response.json()["data"]["results"][0]
    assert "key_strengths" in response.json()["data"]["results"][0]
    assert "suggested_tension_range" in response.json()["data"]["results"][0]
    assert "string_id" in response.json()["data"]["results"][0]


def test_recommendation_log_is_written():
    customer_token = _register_customer_token()

    client.post(
        "/api/v1/recommendations/generate",
        json={
            "skill_level": "intermediate",
            "playing_style": "balanced",
            "budget": {"max": 45},
            "preferred_tension": 25,
            "tension_retention_priority": 4,
        },
        headers=_headers(customer_token),
    )

    with SessionLocal() as db:
        log = db.execute(select(RecommendationLog)).scalar_one_or_none()

    assert log is not None


def test_recommendation_log_keeps_extended_input_snapshot():
    customer_token = _register_customer_token()

    client.post(
        "/api/v1/recommendations/generate",
        json={
            "skill_level": "intermediate",
            "playing_style": "balanced",
            "budget": {"min": 30, "max": 45},
            "preferred_tension": 25,
            "sound_priority": 2,
            "tension_retention_priority": 5,
        },
        headers=_headers(customer_token),
    )

    with SessionLocal() as db:
        log = db.execute(select(RecommendationLog)).scalar_one()

    assert '"budget": {"min": 30.0, "max": 45.0}' in log.input_snapshot
    assert '"sound_priority": 2' in log.input_snapshot
    assert '"tension_retention_priority": 5' in log.input_snapshot


def test_recommendation_uses_imported_item_scores(tmp_path: Path):
    from app.services.string_import_service import import_strings_jsonl

    customer_token = _register_customer_token()
    dataset_path = tmp_path / "badminton_strings_recommender.jsonl"
    rows = [
        {
            "id": "control-max",
            "eid": 201,
            "name": "Control Max",
            "brand": "TestBrand",
            "series": "Control",
            "rating": 4.8,
            "rating_5_scale": 4.8,
            "price": 40,
            "want_count": 50,
            "used_count": 40,
            "review_count_total": 25,
            "gauge": "0.68mm",
            "material": "Nylon",
            "color": "White",
            "top_tags": ["控球好", "耐打"],
            "tags": ["控球好"],
            "popularity_signal": 70,
            "source_url": "https://example.com/control-max",
            "feature_text": "控球好 耐打",
        },
        {
            "id": "repulsion-max",
            "eid": 202,
            "name": "Repulsion Max",
            "brand": "TestBrand",
            "series": "Repulsion",
            "rating": 4.5,
            "rating_5_scale": 4.5,
            "price": 40,
            "want_count": 55,
            "used_count": 44,
            "review_count_total": 20,
            "gauge": "0.65mm",
            "material": "Nylon",
            "color": "Black",
            "top_tags": ["弹性好", "声音清脆"],
            "tags": ["弹性好"],
            "popularity_signal": 71,
            "source_url": "https://example.com/repulsion-max",
            "feature_text": "弹性好 声音清脆",
        },
    ]
    dataset_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )
    import_strings_jsonl(dataset_path)

    response = client.post(
        "/api/v1/recommendations/generate",
        json={
            "skill_level": "advanced",
            "playing_style": "control",
            "budget": {"min": 30, "max": 45},
            "preferred_tension": 25,
            "control_priority": 5,
            "repulsion_priority": 1,
            "tension_retention_priority": 5,
        },
        headers=_headers(customer_token),
    )

    assert response.status_code == 200
    model_names = [item["model_name"] for item in response.json()["data"]["results"]]
    assert "Control Max" in model_names
    assert "Repulsion Max" in model_names
    assert model_names.index("Control Max") < model_names.index("Repulsion Max")


def test_recommendation_rejects_invalid_priorities():
    customer_token = _register_customer_token()

    response = client.post(
        "/api/v1/recommendations/generate",
        json={
            "skill_level": "intermediate",
            "playing_style": "balanced",
            "control_priority": 0,
            "repulsion_priority": 9,
        },
        headers=_headers(customer_token),
    )

    assert response.status_code == 422


def test_recommendation_rejects_legacy_comfort_priority():
    customer_token = _register_customer_token()

    response = client.post(
        "/api/v1/recommendations/generate",
        json={
            "skill_level": "intermediate",
            "playing_style": "balanced",
            "comfort_priority": 5,
        },
        headers=_headers(customer_token),
    )

    assert response.status_code == 422
