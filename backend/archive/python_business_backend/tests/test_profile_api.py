from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import CustomerProfile
from app.db.session import SessionLocal
from app.main import app


client = TestClient(app)


def setup_function():
    from app.services.auth_service import auth_service
    from app.services.profile_service import profile_service

    auth_service.reset()
    profile_service.reset()


def _register_customer() -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )
    access_token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_get_profile_returns_null_when_missing():
    headers = _register_customer()

    response = client.get("/api/v1/profile/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["data"] is None


def test_create_and_get_profile():
    headers = _register_customer()

    payload = {
        "skill_level": "intermediate",
        "playing_style": "balanced",
        "budget": {"min": 30, "max": 45},
        "preferred_tension": 25,
        "sound_priority": 4,
        "tension_retention_priority": 5,
    }

    create_response = client.post(
        "/api/v1/profile/me",
        json=payload,
        headers=headers,
    )

    assert create_response.status_code == 200
    assert create_response.json()["data"]["skill_level"] == "intermediate"
    assert create_response.json()["data"]["budget"]["max"] == 45.0

    with SessionLocal() as db:
        profile = db.execute(select(CustomerProfile)).scalar_one_or_none()

    assert profile is not None
    assert profile.skill_level == "intermediate"
    assert profile.playing_style == "balanced"
    assert profile.sound_priority == 4
    assert profile.tension_retention_priority == 5

    get_response = client.get("/api/v1/profile/me", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["data"]["playing_style"] == "balanced"


def test_update_profile():
    headers = _register_customer()

    client.post(
        "/api/v1/profile/me",
        json={
            "skill_level": "intermediate",
            "playing_style": "balanced",
        },
        headers=headers,
    )

    update_response = client.put(
        "/api/v1/profile/me",
        json={
            "skill_level": "advanced",
            "playing_style": "attacking",
        },
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["data"]["skill_level"] == "advanced"

    with SessionLocal() as db:
        profile = db.execute(select(CustomerProfile)).scalar_one_or_none()

    assert profile is not None
    assert profile.skill_level == "advanced"
    assert profile.playing_style == "attacking"


def test_profile_rejects_invalid_budget_range():
    headers = _register_customer()

    response = client.post(
        "/api/v1/profile/me",
        json={
            "budget": {"min": 60, "max": 40},
            "durability_priority": 6,
        },
        headers=headers,
    )

    assert response.status_code == 422
