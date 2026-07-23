from __future__ import annotations

from datetime import datetime
from datetime import timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import Payment
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.entrypoints.api.dependencies import get_clock
from app.main import app


client = TestClient(app)


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 23, 16, 30, tzinfo=timezone.utc)


def test_analytics_uses_persisted_payments_and_store_local_day(
    monkeypatch,
) -> None:
    login = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60190000000",
            "password": "admin1234",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    with SessionLocal() as db:
        user_id = db.execute(
            select(User.id).where(User.phone_number == "+60190000000")
        ).scalar_one()
        db.add_all(
            [
                Payment(
                    id="payment-pending-booking",
                    user_id=user_id,
                    method="online_banking",
                    status="pending",
                    amount=Decimal("40.00"),
                    payment_type="booking_payment",
                    reference="PAY-PENDING",
                    created_at=datetime(2026, 7, 23, 14, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 7, 23, 14, tzinfo=timezone.utc),
                ),
                Payment(
                    id="payment-pending-topup",
                    user_id=user_id,
                    method="online_banking",
                    status="pending",
                    amount=Decimal("20.00"),
                    payment_type="wallet_top_up",
                    reference="TOP-PENDING",
                    created_at=datetime(2026, 7, 23, 15, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 7, 23, 15, tzinfo=timezone.utc),
                ),
                Payment(
                    id="payment-paid-today",
                    user_id=user_id,
                    method="wallet_balance",
                    status="paid",
                    amount=Decimal("48.50"),
                    payment_type="booking_payment",
                    reference="PAY-TODAY",
                    created_at=datetime(2026, 7, 23, 15, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 7, 23, 16, 5, tzinfo=timezone.utc),
                ),
                Payment(
                    id="payment-paid-yesterday",
                    user_id=user_id,
                    method="online_banking",
                    status="paid",
                    amount=Decimal("60.00"),
                    payment_type="booking_payment",
                    reference="PAY-YESTERDAY",
                    created_at=datetime(2026, 7, 23, 15, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 7, 23, 15, 55, tzinfo=timezone.utc),
                ),
                Payment(
                    id="payment-paid-topup",
                    user_id=user_id,
                    method="online_banking",
                    status="paid",
                    amount=Decimal("100.00"),
                    payment_type="wallet_top_up",
                    reference="TOP-TODAY",
                    created_at=datetime(2026, 7, 23, 16, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 7, 23, 16, 10, tzinfo=timezone.utc),
                ),
            ]
        )
        db.commit()

    monkeypatch.setattr(
        get_settings(),
        "store_timezone",
        "Asia/Kuala_Lumpur",
    )
    app.dependency_overrides[get_clock] = FixedClock
    try:
        response = client.get(
            "/api/admin/analytics/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_clock, None)

    assert response.status_code == 200
    summary = response.json()
    assert summary["pending_payment_count"] == 2
    assert summary["today_revenue"] == 48.5
    assert summary["workload_mix"][0] == {
        "label": "Pending payment",
        "value": 2,
    }
