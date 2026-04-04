from __future__ import annotations

import os

import pytest


os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:////tmp/stringsense_test.db")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-that-is-long-enough-for-sha256",
)
os.environ.setdefault("SEED_ADMIN_PASSWORD", "admin123")


@pytest.fixture(autouse=True)
def reset_test_database() -> None:
    from app.db.session import create_all_tables
    from app.db.session import drop_all_tables
    from app.db.session import SessionLocal
    from app.services.auth_service import auth_service

    drop_all_tables()
    create_all_tables()
    with SessionLocal() as db:
        auth_service.ensure_seed_admin(db)
        db.commit()
    yield
