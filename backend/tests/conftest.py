from __future__ import annotations

import os
from collections.abc import Generator

import pytest


os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:////tmp/stringsense_unified_test.db",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-that-is-long-enough-for-sha256",
)
os.environ.setdefault("JWT_ISSUER", "stringsense-python-api-test")
os.environ.setdefault("SEED_ADMIN_ENABLED", "true")
os.environ.setdefault("SEED_ADMIN_USERNAME", "system-admin")
os.environ.setdefault("SEED_ADMIN_PHONE_NUMBER", "+60190000000")
os.environ.setdefault("SEED_ADMIN_PASSWORD", "admin1234")
os.environ.setdefault("AI_INTERNAL_API_KEY", "test-ai-internal-key")
os.environ.setdefault("UPLOAD_ROOT_PATH", "/tmp/stringsense_test_uploads")
os.environ["OPENWA_ENABLED"] = "false"


@pytest.fixture(autouse=True)
def reset_unified_backend_db() -> Generator[None, None, None]:
    from app.adapters.persistence.sqlalchemy.seed import ensure_catalog_seeded
    from app.adapters.persistence.sqlalchemy.seed import ensure_seed_users
    from app.adapters.persistence.sqlalchemy.seed import ensure_store_defaults
    from app.adapters.persistence.sqlalchemy.models import StoreBusinessHours
    from app.adapters.persistence.sqlalchemy.session import SessionLocal
    from app.adapters.persistence.sqlalchemy.session import create_all_tables
    from app.adapters.persistence.sqlalchemy.session import drop_all_tables
    from app.entrypoints.api.routes.auth_routes import _login_limiter
    from app.entrypoints.api.routes.auth_routes import _reset_limiter
    from app.entrypoints.api.routes.auth_routes import _reset_request_limiter
    from app.entrypoints.api.routes.agent_routes import _agent_limiter

    _login_limiter.clear()
    _reset_request_limiter.clear()
    _reset_limiter.clear()
    _agent_limiter.clear()

    drop_all_tables()
    create_all_tables()
    with SessionLocal() as db:
        ensure_seed_users(db)
        ensure_catalog_seeded(db)
        ensure_store_defaults(db)
        business_hours = db.get(StoreBusinessHours, "main")
        assert business_hours is not None
        business_hours.days_json = [
            {
                "day": day,
                "is_open": True,
                "open_time": "09:00",
                "close_time": "18:00",
                "break_start": "13:00",
                "break_end": "14:00",
                "slot_duration_minutes": 30,
                "max_bookings_per_slot": 2,
            }
            for day in (
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            )
        ]
        db.commit()
    yield
