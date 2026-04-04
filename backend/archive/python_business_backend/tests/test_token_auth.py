from app.core.security import create_access_token
from app.integrations.token_auth import verify_access_token


def test_signed_access_token_returns_customer_payload():
    token = create_access_token(
        subject="customer-1",
        auth_user_id="auth-customer-1",
        role="customer",
        phone_number="0123456789",
    )
    payload = verify_access_token(token)

    assert payload is not None
    assert payload["role"] == "customer"
    assert payload["phone_number"] == "0123456789"
    assert payload["auth_user_id"] == "auth-customer-1"


def test_signed_access_token_returns_admin_payload():
    token = create_access_token(
        subject="admin-1",
        auth_user_id="auth-admin-1",
        role="admin",
        phone_number="0190000000",
    )
    payload = verify_access_token(token)

    assert payload is not None
    assert payload["role"] == "admin"
    assert payload["phone_number"] == "0190000000"


def test_invalid_token_returns_none():
    payload = verify_access_token("invalid-token")

    assert payload is None
