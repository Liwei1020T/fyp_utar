from __future__ import annotations

import os

import pytest


os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:////tmp/stringsense_unified_test.db",
)
os.environ.setdefault("AUTO_CREATE_SCHEMA", "true")
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


@pytest.fixture(autouse=True)
def reset_unified_backend_db() -> None:
    from stringsense_backend.db.seed import ensure_catalog_seeded
    from stringsense_backend.db.seed import ensure_seed_users
    from stringsense_backend.db.seed import ensure_store_defaults
    from stringsense_backend.db.session import SessionLocal
    from stringsense_backend.db.session import create_all_tables
    from stringsense_backend.db.session import drop_all_tables

    drop_all_tables()
    create_all_tables()
    with SessionLocal() as db:
        ensure_seed_users(db)
        ensure_catalog_seeded(db)
        ensure_store_defaults(db)
        db.commit()
    yield
