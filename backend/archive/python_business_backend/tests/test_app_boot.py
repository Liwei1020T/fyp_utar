from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import AppUser
from app.db.session import SessionLocal
from app.main import app


def test_versioned_health_check():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_startup_seeds_admin_idempotently():
    with TestClient(app):
        pass
    with TestClient(app):
        pass

    with SessionLocal() as db:
        admins = (
            db.execute(
                select(AppUser).where(AppUser.phone_number == "0190000000")
            )
            .scalars()
            .all()
        )

    assert len(admins) == 1
    assert admins[0].role == "admin"
