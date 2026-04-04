from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_dev_auth_is_disabled_by_default():
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"role": "customer"},
    )

    assert response.status_code == 404


def test_dev_auth_customer_session(monkeypatch):
    monkeypatch.setattr(settings, "enable_dev_auth", True)

    response = client.post(
        "/api/v1/auth/dev-login",
        json={"role": "customer"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["access_token"].count(".") == 2
    assert response.json()["data"]["role"] == "customer"
    assert response.json()["data"]["phone_number"]


def test_dev_auth_admin_session(monkeypatch):
    monkeypatch.setattr(settings, "enable_dev_auth", True)

    response = client.post(
        "/api/v1/auth/dev-login",
        json={"role": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["access_token"].count(".") == 2
    assert response.json()["data"]["role"] == "admin"
    assert response.json()["data"]["phone_number"] == "0190000000"
