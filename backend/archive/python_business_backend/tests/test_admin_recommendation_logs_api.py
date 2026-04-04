from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(token: str) -> dict[str, str]:
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


def _admin_token() -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0190000000",
            "password": "admin123",
        },
    )
    return response.json()["data"]["access_token"]


def test_admin_can_view_recommendation_logs():
    customer_token = _register_customer_token()
    admin_token = _admin_token()

    client.post(
        "/api/v1/recommendations/generate",
        json={
            "skill_level": "intermediate",
            "playing_style": "balanced",
            "preferred_tension": 25,
        },
        headers=_headers(customer_token),
    )

    response = client.get(
        "/api/v1/admin/recommendation-logs",
        headers=_headers(admin_token),
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["phone_number"] == "0123456789"


def test_admin_recommendation_logs_support_phone_filter_and_pagination():
    first_customer_token = _register_customer_token()
    second_customer_token = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Lee Jia",
            "phone_number": "0123456799",
            "password": "secret123",
        },
    ).json()["data"]["access_token"]
    admin_token = _admin_token()

    client.post(
        "/api/v1/recommendations/generate",
        json={"skill_level": "intermediate", "playing_style": "balanced"},
        headers=_headers(first_customer_token),
    )
    client.post(
        "/api/v1/recommendations/generate",
        json={"skill_level": "advanced", "playing_style": "control"},
        headers=_headers(second_customer_token),
    )

    response = client.get(
        "/api/v1/admin/recommendation-logs?phone_number=0123456799&limit=1",
        headers=_headers(admin_token),
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["phone_number"] == "0123456799"
    assert response.json()["pagination"]["total"] == 1
