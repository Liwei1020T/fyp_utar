from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import CheckInToken
from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.models import RecommendationLog
from app.adapters.persistence.sqlalchemy.models import RecommendationRun
from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import UserPreferenceMatrix
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_password_reset_repository import (
    SqlAlchemyPasswordResetRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_recommendation_log_repository import (
    SqlAlchemyRecommendationLogRepository,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.main import app


client = TestClient(app)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(phone_number: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"player-{phone_number[-4:]}",
            "phone_number": phone_number,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _login_admin() -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60190000000",
            "password": "admin1234",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_recommendation_rolls_back_cache_when_log_write_fails(monkeypatch) -> None:
    token = _register("+60123330001")
    profile = client.put(
        "/api/profile",
        headers=_headers(token),
        json={
            "skill_level": "advanced",
            "playing_style": "attacking",
            "budget_tier": "between_30_50",
            "preferred_tension": 27,
            "game_type": "doubles",
            "frequency_per_week": 4,
            "pref_attack": 5,
            "pref_comfort": 3,
            "pref_control": 4,
            "pref_durability": 3,
            "pref_elasticity": 5,
            "pref_sound": 4,
            "pref_string_movement": 3,
            "pref_tension_retention": 4,
            "pref_value_for_money": 3,
        },
    )
    assert profile.status_code == 200
    tracked_models = (
        UserPreferenceMatrix,
        RecommendationScoreCache,
        RecommendationRun,
        RecommendationLog,
    )
    with SessionLocal() as db:
        counts_before = {
            model: db.scalar(select(func.count()).select_from(model))
            for model in tracked_models
        }

    def fail_log_write(*args, **kwargs) -> None:
        raise RuntimeError("forced recommendation log failure")

    monkeypatch.setattr(
        SqlAlchemyRecommendationLogRepository,
        "create_log",
        fail_log_write,
    )
    with pytest.raises(RuntimeError, match="forced recommendation log failure"):
        client.post(
            "/api/recommendations/generate",
            headers=_headers(token),
            json={"top_n": 3},
        )

    with SessionLocal() as db:
        for model in tracked_models:
            assert (
                db.scalar(select(func.count()).select_from(model))
                == counts_before[model]
            )


def test_password_reset_rolls_back_password_when_code_write_fails(monkeypatch) -> None:
    phone_number = "+60123330002"
    _register(phone_number)
    monkeypatch.setattr(
        get_settings(),
        "password_reset_dev_preview_enabled",
        True,
    )
    code_response = client.post(
        "/api/auth/forgot-password/request-code",
        json={"phone_number": phone_number},
    )
    code = code_response.json()["dev_code_preview"]
    assert code

    def fail_code_write(*args, **kwargs) -> None:
        raise RuntimeError("forced reset-code failure")

    monkeypatch.setattr(
        SqlAlchemyPasswordResetRepository,
        "mark_used",
        fail_code_write,
    )
    with pytest.raises(RuntimeError, match="forced reset-code failure"):
        client.post(
            "/api/auth/forgot-password/reset",
            json={
                "phone_number": phone_number,
                "verification_code": code,
                "new_password": "changed123",
            },
        )

    old_login = client.post(
        "/api/auth/login",
        json={"phone_number": phone_number, "password": "secret123"},
    )
    new_login = client.post(
        "/api/auth/login",
        json={"phone_number": phone_number, "password": "changed123"},
    )
    assert old_login.status_code == 200
    assert new_login.status_code == 401
    with SessionLocal() as db:
        reset_code = db.scalar(select(PasswordResetCode))
        assert reset_code is not None
        assert reset_code.used_at is None


def test_check_in_rolls_back_consumed_token_when_booking_write_fails(
    monkeypatch,
) -> None:
    player_token = _register("+60123330003")
    strings = client.get("/api/strings", headers=_headers(player_token))
    booking = client.post(
        "/api/bookings",
        headers=_headers(player_token),
        json={"string_id": strings.json()["items"][0]["id"]},
    )
    booking_id = booking.json()["id"]
    token_response = client.post(
        f"/api/bookings/{booking_id}/check-in-token",
        headers=_headers(player_token),
    )
    raw_token = token_response.json()["token"]

    def fail_booking_write(*args, **kwargs):
        raise RuntimeError("forced booking write failure")

    monkeypatch.setattr(
        SqlAlchemyBookingRepository,
        "update_status",
        fail_booking_write,
    )
    with pytest.raises(RuntimeError, match="forced booking write failure"):
        client.post(
            "/api/admin/check-in/confirm",
            headers=_headers(_login_admin()),
            json={"token": raw_token},
        )

    with SessionLocal() as db:
        stored_token = db.scalar(select(CheckInToken))
        stored_booking = db.get(Booking, booking_id)
        assert stored_token is not None
        assert stored_token.used_at is None
        assert stored_booking is not None
        assert stored_booking.status == "awaiting_dropoff"
