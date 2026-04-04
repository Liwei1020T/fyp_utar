import importlib
import os

from fastapi.testclient import TestClient

from ai_service.core.config import get_ai_settings


os.environ["AI_INTERNAL_API_KEY"] = "test-ai-internal-key"
get_ai_settings.cache_clear()
app = importlib.import_module("ai_service.app").app


client = TestClient(app)
HEADERS = {"x-internal-api-key": os.environ["AI_INTERNAL_API_KEY"]}


def test_ai_health_endpoint_reports_loaded_matrix():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai"
    assert data["matrix_loaded"] >= 1


def test_internal_recommendation_endpoint_returns_ranked_results():
    response = client.post(
        "/internal/ai/recommend",
        headers=HEADERS,
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
            "top_n": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["algorithm_version"] == "practical_matrix_v8_rule_content_v1"
    assert len(data["results"]) == 3
    assert data["results"][0]["rank"] == 1
    assert isinstance(data["results"][0]["reasons"], list)
    assert "string_name" in data["results"][0]


def test_internal_strings_endpoint_requires_internal_key():
    response = client.get("/internal/ai/strings")

    assert response.status_code == 401
