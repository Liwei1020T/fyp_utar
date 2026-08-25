from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PNG_BYTES = b"\x89PNG\r\n\x1a\nqr-test"


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
    assert "service_fee" not in quote
    assert quote["total_amount"] == quote["string_fee"]
    assert quote["wallet_balance"] == 0
    assert quote["active_payment"] is None

    forbidden_response = client.get(
        f"/api/payments/bookings/{booking_id}/quote",
        headers=_headers(other_token),
    )
    assert forbidden_response.status_code == 403

    qr_response = client.post(
        "/api/admin/store-settings/payment-qr",
        headers=_headers(admin_response.json()["access_token"]),
        files={"photo": ("shop-qr.png", PNG_BYTES, "image/png")},
    )
    assert qr_response.status_code == 200

    stale_quote_response = client.post(
        f"/api/payments/bookings/{booking_id}",
        headers=_headers(token),
        data={
            "method": "qr_transfer",
            "expected_amount": str(quote["total_amount"] + 1),
        },
        files={"proof": ("payment.png", PNG_BYTES, "image/png")},
    )
    assert stale_quote_response.status_code == 409

    payment_response = client.post(
        f"/api/payments/bookings/{booking_id}",
        headers=_headers(token),
        data={
            "method": "qr_transfer",
            "expected_amount": str(quote["total_amount"]),
        },
        files={"proof": ("payment.png", PNG_BYTES, "image/png")},
    )
    assert payment_response.status_code == 200
    assert payment_response.json()["method"] == "qr_transfer"
    assert payment_response.json()["amount"] == quote["string_fee"]
    assert payment_response.json()["proof_url"]

    active_quote_response = client.get(
        f"/api/payments/bookings/{booking_id}/quote",
        headers=_headers(token),
    )
    assert active_quote_response.status_code == 200
    active_quote = active_quote_response.json()
    assert active_quote["total_amount"] == payment_response.json()["amount"]
    assert active_quote["active_payment"]["id"] == payment_response.json()["id"]


def test_admin_payment_qr_can_be_replaced_deleted_and_downloaded() -> None:
    token = _register("+60125550211")
    admin_response = client.post(
        "/api/auth/login",
        json={"phone_number": "+60190000000", "password": "admin1234"},
    )
    assert admin_response.status_code == 200
    admin_token = admin_response.json()["access_token"]

    initial_settings = client.get(
        "/api/store-settings",
        headers=_headers(token),
    )
    assert initial_settings.status_code == 200
    assert initial_settings.json()["payment_qr_url"] is None

    first_upload = client.post(
        "/api/admin/store-settings/payment-qr",
        headers=_headers(admin_token),
        files={"photo": ("first.png", PNG_BYTES, "image/png")},
    )
    assert first_upload.status_code == 200
    first_url = first_upload.json()["payment_qr_url"]
    assert "/api/media/payment-qr/" in first_url

    downloaded = client.get(f"{first_url}&download=1")
    assert downloaded.status_code == 200
    assert "attachment" in downloaded.headers["content-disposition"]

    second_upload = client.post(
        "/api/admin/store-settings/payment-qr",
        headers=_headers(admin_token),
        files={"photo": ("second.png", PNG_BYTES + b"2", "image/png")},
    )
    assert second_upload.status_code == 200
    assert second_upload.json()["payment_qr_url"] != first_url

    delete_response = client.delete(
        "/api/admin/store-settings/payment-qr",
        headers=_headers(admin_token),
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["payment_qr_url"] is None

    blocked_top_up = client.post(
        "/api/wallet/top-ups",
        headers=_headers(token),
        data={"amount": "20", "method": "qr_transfer"},
        files={"proof": ("payment.png", PNG_BYTES, "image/png")},
    )
    assert blocked_top_up.status_code == 400
    assert "QR payment is not configured" in blocked_top_up.json()["error"]["message"]

    invalid_upload = client.post(
        "/api/admin/store-settings/payment-qr",
        headers=_headers(admin_token),
        files={"photo": ("invalid.png", b"not-an-image", "image/png")},
    )
    assert invalid_upload.status_code == 400


def test_cash_booking_payment_and_top_up_wait_for_admin_confirmation() -> None:
    token = _register("+60125550221")
    admin_response = client.post(
        "/api/auth/login",
        json={"phone_number": "+60190000000", "password": "admin1234"},
    )
    assert admin_response.status_code == 200
    admin_token = admin_response.json()["access_token"]
    inventory_response = client.get(
        "/api/admin/inventory/strings",
        headers=_headers(admin_token),
    )
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

    payment_response = client.post(
        f"/api/payments/bookings/{booking_response.json()['id']}",
        headers=_headers(token),
        data={"method": "cash"},
    )
    assert payment_response.status_code == 200
    assert payment_response.json()["method"] == "cash"
    assert payment_response.json()["status"] == "pending"
    assert payment_response.json()["proof_url"] is None

    top_up_response = client.post(
        "/api/wallet/top-ups",
        headers=_headers(token),
        data={"amount": "50", "method": "cash"},
    )
    assert top_up_response.status_code == 200
    assert top_up_response.json()["method"] == "cash"
    assert top_up_response.json()["status"] == "pending"
    assert top_up_response.json()["proof_url"] is None

    pending_wallet = client.get("/api/wallet", headers=_headers(token))
    assert pending_wallet.json()["available_balance"] == 0
    assert pending_wallet.json()["pending_top_up"] == 50

    approve_response = client.patch(
        f"/api/admin/payments/{top_up_response.json()['id']}",
        headers=_headers(admin_token),
        json={"status": "paid"},
    )
    assert approve_response.status_code == 200
    funded_wallet = client.get("/api/wallet", headers=_headers(token))
    assert funded_wallet.json()["available_balance"] == 50
    assert funded_wallet.json()["pending_top_up"] == 0
