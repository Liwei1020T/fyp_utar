import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import String
from app.db.session import SessionLocal
from app.main import app


client = TestClient(app)


def _admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer admin-token"}


def _customer_headers() -> dict[str, str]:
    return {"Authorization": "Bearer customer-token"}


def _patch_customer(monkeypatch):
    from app.api.deps import auth as auth_deps

    monkeypatch.setattr(
        auth_deps,
        "verify_access_token",
        lambda token: (
            {
                "sub": "auth-user-1",
                "auth_user_id": "customer-ext-1",
                "phone_number": "0123456789",
                "role": "customer",
            }
            if token == "customer-token"
            else {
                "sub": "auth-admin-1",
                "auth_user_id": "admin-ext-1",
                "phone_number": "0190000000",
                "role": "admin",
            }
        ),
    )


def setup_function():
    from app.services.string_service import string_service

    string_service.reset()


def test_list_strings_returns_seeded_items(monkeypatch):
    _patch_customer(monkeypatch)
    response = client.get("/api/v1/strings", headers=_customer_headers())

    assert response.status_code == 200
    assert len(response.json()["data"]) >= 2


def test_get_string_detail(monkeypatch):
    _patch_customer(monkeypatch)

    list_response = client.get("/api/v1/strings", headers=_customer_headers())
    string_id = list_response.json()["data"][0]["id"]

    response = client.get(f"/api/v1/strings/{string_id}", headers=_customer_headers())

    assert response.status_code == 200
    assert response.json()["data"]["id"] == string_id


def test_admin_can_create_update_and_delete_string(monkeypatch):
    _patch_customer(monkeypatch)

    create_response = client.post(
        "/api/v1/admin/strings",
        json={
            "brand": "Li-Ning",
            "model_name": "No.1",
            "price": 35,
            "recommended_tension_min": 20,
            "recommended_tension_max": 28,
        },
        headers=_admin_headers(),
    )

    assert create_response.status_code == 200
    string_id = create_response.json()["data"]["id"]

    update_response = client.put(
        f"/api/v1/admin/strings/{string_id}",
        json={
            "brand": "Li-Ning",
            "model_name": "No.1 Boost",
            "price": 38,
        },
        headers=_admin_headers(),
    )

    assert update_response.status_code == 200
    assert update_response.json()["data"]["model_name"] == "No.1 Boost"

    with SessionLocal() as db:
        string_item = db.execute(
            select(String).where(String.id == string_id)
        ).scalar_one_or_none()

    assert string_item is not None
    assert string_item.model_name == "No.1 Boost"

    delete_response = client.delete(
        f"/api/v1/admin/strings/{string_id}",
        headers=_admin_headers(),
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["is_active"] is False

    with SessionLocal() as db:
        string_item = db.execute(
            select(String).where(String.id == string_id)
        ).scalar_one_or_none()

    assert string_item is not None
    assert string_item.is_active is False


def test_admin_can_list_strings(monkeypatch):
    _patch_customer(monkeypatch)

    response = client.get("/api/v1/admin/strings", headers=_admin_headers())

    assert response.status_code == 200
    assert len(response.json()["data"]) >= 2


def test_public_strings_support_search_sort_and_pagination(monkeypatch):
    _patch_customer(monkeypatch)

    client.post(
        "/api/v1/admin/strings",
        json={
            "brand": "Li-Ning",
            "model_name": "Aeronaut Control",
            "price": 45,
            "recommended_tension_min": 20,
            "recommended_tension_max": 28,
        },
        headers=_admin_headers(),
    )

    response = client.get(
        "/api/v1/strings?search=yo&sort_by=price&sort_order=desc&limit=1&offset=0",
        headers=_customer_headers(),
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["brand"] == "Yonex"
    assert response.json()["pagination"]["total"] == 2
    assert response.json()["pagination"]["limit"] == 1


def test_strings_require_authentication(monkeypatch):
    _patch_customer(monkeypatch)

    response = client.get("/api/v1/strings")

    assert response.status_code == 401


def test_admin_strings_support_active_filter_and_search(monkeypatch):
    _patch_customer(monkeypatch)

    create_response = client.post(
        "/api/v1/admin/strings",
        json={
            "brand": "Ashaway",
            "model_name": "Rally 21",
            "price": 30,
            "recommended_tension_min": 20,
            "recommended_tension_max": 27,
        },
        headers=_admin_headers(),
    )
    string_id = create_response.json()["data"]["id"]
    client.delete(f"/api/v1/admin/strings/{string_id}", headers=_admin_headers())

    inactive_response = client.get(
        "/api/v1/admin/strings?is_active=false&search=ash",
        headers=_admin_headers(),
    )

    assert inactive_response.status_code == 200
    assert len(inactive_response.json()["data"]) == 1
    assert inactive_response.json()["data"][0]["model_name"] == "Rally 21"


def test_admin_can_import_strings_from_json(monkeypatch, tmp_path: Path):
    _patch_customer(monkeypatch)
    payload = [
        {
            "id": "json-import-1",
            "brand": "Victor",
            "name": "VBS 66 Nano",
            "price": 34,
            "top_tags": ["弹性好", "声音清脆"],
        }
    ]
    import_file = tmp_path / "strings.json"
    import_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with import_file.open("rb") as handle:
        response = client.post(
            "/api/v1/admin/strings/import",
            headers=_admin_headers(),
            files={"file": ("strings.json", handle, "application/json")},
        )

    assert response.status_code == 200
    assert response.json()["data"]["created_count"] == 1
    assert response.json()["data"]["error_count"] == 0

    with SessionLocal() as db:
        imported = db.execute(
            select(String).where(String.external_id == "json-import-1")
        ).scalar_one_or_none()

    assert imported is not None
    assert imported.brand == "Victor"
