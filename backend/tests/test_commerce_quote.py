from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(phone_number: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"quote-{phone_number[-4:]}",
            "phone_number": phone_number,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_booking_payment_quote_is_owned_and_uses_active_ledger_amount() -> None:
    token = _register("+60125550201")
    other_token = _register("+60125550202")
    admin_response = client.post(
        "/api/auth/login",
        json={"phone_number": "+60190000000", "password": "admin1234"},
    )
    assert admin_response.status_code == 200
    inventory_response = client.get(
        "/api/admin/inventory/strings",
        headers=_headers(admin_response.json()["access_token"]),
    )
    assert inventory_response.status_code == 200
    priced_string = next(
        item
        for item in inventory_response.json()["items"]
        if item["pricing_mode"] == "fixed_price" and item["selling_price"] > 0
    )

    booking_response = client.post(
        "/api/bookings",
        headers=_headers(token),
        json={
            "string_id": priced_string["id"],
            "racket_brand": "Yonex",
            "racket_model": "Astrox 99",
            "requested_tension": 26,
        },
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]

    quote_response = client.get(
        f"/api/payments/bookings/{booking_id}/quote",
        headers=_headers(token),
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()
    assert quote["booking_id"] == booking_id
    assert quote["string_fee"] > 0
    assert quote["service_fee"] == 0
    assert quote["total_amount"] == quote["string_fee"]
    assert quote["wallet_balance"] == 0
    assert quote["active_payment"] is None

    forbidden_response = client.get(
        f"/api/payments/bookings/{booking_id}/quote",
        headers=_headers(other_token),
    )
    assert forbidden_response.status_code == 403

    stale_quote_response = client.post(
        f"/api/payments/bookings/{booking_id}",
        headers=_headers(token),
        json={
            "method": "online_banking",
            "expected_amount": quote["total_amount"] + 1,
        },
    )
    assert stale_quote_response.status_code == 409

    payment_response = client.post(
        f"/api/payments/bookings/{booking_id}",
        headers=_headers(token),
        json={
            "method": "online_banking",
            "expected_amount": quote["total_amount"],
        },
    )
    assert payment_response.status_code == 200

    active_quote_response = client.get(
        f"/api/payments/bookings/{booking_id}/quote",
        headers=_headers(token),
    )
    assert active_quote_response.status_code == 200
    active_quote = active_quote_response.json()
    assert active_quote["total_amount"] == payment_response.json()["amount"]
    assert active_quote["active_payment"]["id"] == payment_response.json()["id"]
