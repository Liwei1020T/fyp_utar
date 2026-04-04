from fastapi.testclient import TestClient

from ai_service.main import app


client = TestClient(app)
HEADERS = {"x-internal-api-key": "dev-ai-internal-key"}


def test_internal_recommend_endpoint_returns_ranked_results():
    response = client.post(
        "/internal/ai/recommend",
        headers=HEADERS,
        json={
            "profile": {
                "skill_level": "intermediate",
                "playing_style": "balanced",
            },
            "request": {
                "budget": {"min": 30, "max": 45},
                "preferred_tension": 25,
                "control_priority": 5,
                "repulsion_priority": 4,
                "durability_priority": 4,
                "sound_priority": 3,
                "tension_retention_priority": 4,
            },
            "catalog": [
                {
                    "id": "bg80",
                    "brand": "Yonex",
                    "model_name": "BG80",
                    "price": 39,
                    "recommended_tension_min": 20,
                    "recommended_tension_max": 28,
                    "repulsion_score": 4.3,
                    "durability_score": 4.4,
                    "control_score": 4.6,
                    "sound_score": 4.5,
                    "tension_retention_score": 3.8,
                    "value_score": 4.0,
                },
                {
                    "id": "exbolt63",
                    "brand": "Yonex",
                    "model_name": "Exbolt 63",
                    "price": 42,
                    "recommended_tension_min": 20,
                    "recommended_tension_max": 27,
                    "repulsion_score": 4.7,
                    "durability_score": 3.4,
                    "control_score": 3.8,
                    "sound_score": 4.6,
                    "tension_retention_score": 3.2,
                    "value_score": 4.1,
                },
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["algorithm_version"] == "fyp1-rule-based-content-v4"
    assert data["results"][0]["rank"] == 1
    assert data["results"][0]["string_id"] == "bg80"


def test_internal_review_analysis_returns_aspect_summary():
    response = client.post(
        "/internal/ai/reviews/analyze",
        headers=HEADERS,
        json={
            "reviews": [
                {
                    "review_text": "Great control and very durable string, but a bit muted on sound.",
                }
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["review_count"] == 1
    assert any(item["aspect"] == "control" for item in data["extracted_aspects"])
