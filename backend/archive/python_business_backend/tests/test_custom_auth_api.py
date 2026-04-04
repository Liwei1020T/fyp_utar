from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete
from sqlalchemy import select

from app.core.config import settings
from app.core.constants import UserRole
from app.core.exceptions import ConflictError
from app.db.models import AppUser
from app.db.session import SessionLocal
from app.main import app


client = TestClient(app)


def setup_function():
    from app.services.auth_service import auth_service

    auth_service.reset()


def test_customer_can_register_with_phone_and_password():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "customer"
    assert response.json()["data"]["phone_number"] == "0123456789"
    assert response.json()["data"]["access_token"].count(".") == 2

    with SessionLocal() as db:
        user = db.execute(
            select(AppUser).where(AppUser.phone_number == "0123456789")
        ).scalar_one_or_none()

    assert user is not None
    assert user.full_name == "Tan Wei Jie"
    assert user.role == "customer"
    assert user.password_hash != "secret123"


def test_customer_can_login_with_phone_and_password():
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "customer"
    assert response.json()["data"]["phone_number"] == "0123456789"


def test_customer_cannot_register_same_phone_number_twice():
    payload = {
        "full_name": "Tan Wei Jie",
        "phone_number": "0123456789",
        "password": "secret123",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Phone number already registered"


def test_register_rejects_invalid_phone_number_and_short_password():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "12345",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_request_password_reset_code_is_generic_for_existing_user_by_default():
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/v1/auth/forgot-password/request-code",
        json={"phone_number": "0123456789"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent if the account exists"
    assert response.json()["data"] == {}


def test_request_password_reset_code_returns_dev_preview_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/v1/auth/forgot-password/request-code",
        json={"phone_number": "0123456789"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent if the account exists"
    assert len(response.json()["data"]["dev_code_preview"]) == 6


def test_request_password_reset_code_is_generic_for_unknown_phone():
    response = client.post(
        "/api/v1/auth/forgot-password/request-code",
        json={"phone_number": "0111111111"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent if the account exists"
    assert response.json()["data"] == {}


def test_customer_can_reset_password_with_verification_code(monkeypatch):
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )
    request_code_response = client.post(
        "/api/v1/auth/forgot-password/request-code",
        json={"phone_number": "0123456789"},
    )
    verification_code = request_code_response.json()["data"]["dev_code_preview"]

    reset_response = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={
            "phone_number": "0123456789",
            "verification_code": verification_code,
            "new_password": "newpass456",
        },
    )

    old_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )
    new_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0123456789",
            "password": "newpass456",
        },
    )

    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "Password reset successful"
    assert old_login_response.status_code == 401
    assert new_login_response.status_code == 200


def test_admin_can_reset_password_with_verification_code(monkeypatch):
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)

    request_code_response = client.post(
        "/api/v1/auth/forgot-password/request-code",
        json={"phone_number": "0190000000"},
    )
    verification_code = request_code_response.json()["data"]["dev_code_preview"]

    reset_response = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={
            "phone_number": "0190000000",
            "verification_code": verification_code,
            "new_password": "admin456",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0190000000",
            "password": "admin456",
        },
    )

    assert reset_response.status_code == 200
    assert login_response.status_code == 200


def test_reset_password_rejects_invalid_verification_code(monkeypatch):
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )
    client.post(
        "/api/v1/auth/forgot-password/request-code",
        json={"phone_number": "0123456789"},
    )

    response = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={
            "phone_number": "0123456789",
            "verification_code": "000000",
            "new_password": "newpass456",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification code"


def test_reset_password_rejects_reused_verification_code(monkeypatch):
    monkeypatch.setattr(settings, "password_reset_dev_preview_enabled", True)

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Tan Wei Jie",
            "phone_number": "0123456789",
            "password": "secret123",
        },
    )
    request_code_response = client.post(
        "/api/v1/auth/forgot-password/request-code",
        json={"phone_number": "0123456789"},
    )
    verification_code = request_code_response.json()["data"]["dev_code_preview"]

    first_reset_response = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={
            "phone_number": "0123456789",
            "verification_code": verification_code,
            "new_password": "newpass456",
        },
    )
    second_reset_response = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={
            "phone_number": "0123456789",
            "verification_code": verification_code,
            "new_password": "newpass789",
        },
    )

    assert first_reset_response.status_code == 200
    assert second_reset_response.status_code == 400
    assert (
        second_reset_response.json()["detail"] == "Invalid or expired verification code"
    )


def test_admin_can_login_with_seeded_phone_and_password():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0190000000",
            "password": "admin123",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "admin"

    with SessionLocal() as db:
        admin = db.execute(
            select(AppUser).where(AppUser.phone_number == "0190000000")
        ).scalar_one_or_none()

    assert admin is not None
    assert admin.role == "admin"


def test_auth_me_returns_current_user():
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0190000000",
            "password": "admin123",
        },
    )
    access_token = login_response.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "admin"
    assert response.json()["data"]["phone_number"] == "0190000000"
    assert "email" not in response.json()["data"]


def test_auth_me_rejects_tampered_token():
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "0190000000",
            "password": "admin123",
        },
    )
    access_token = login_response.json()["data"]["access_token"]
    tampered_token = f"{access_token}tampered"

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )

    assert response.status_code == 401


def test_seed_admin_is_create_only(monkeypatch):
    from app.core.security import verify_password
    from app.services.auth_service import auth_service

    with SessionLocal() as db:
        admin = auth_service.ensure_seed_admin(db)
        db.commit()
        db.refresh(admin)
        original_hash = admin.password_hash

    monkeypatch.setattr(settings, "seed_admin_password", "different123")

    with SessionLocal() as db:
        admin = auth_service.ensure_seed_admin(db)
        db.commit()
        db.refresh(admin)
        assert admin.password_hash == original_hash
        assert verify_password("admin123", admin.password_hash)


def test_seed_admin_rejects_non_admin_conflict():
    from app.services.auth_service import auth_service

    with SessionLocal() as db:
        db.execute(
            delete(AppUser).where(
                AppUser.phone_number == settings.seed_admin_phone_number
            )
        )
        db.add(
            AppUser(
                full_name="Existing Customer",
                phone_number=settings.seed_admin_phone_number,
                password_hash="pbkdf2_sha256$1$00$11",
                role=UserRole.CUSTOMER.value,
            )
        )
        db.commit()

        with pytest.raises(ConflictError):
            auth_service.ensure_seed_admin(db)
