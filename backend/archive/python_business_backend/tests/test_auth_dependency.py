from fastapi import Depends
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user


app = FastAPI()


@app.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    return {"user": user}


client = TestClient(app)


def test_protected_route_rejects_missing_token():
    response = client.get("/protected")

    assert response.status_code == 401


def test_protected_route_accepts_verified_token(monkeypatch):
    from app.api.deps import auth as auth_deps

    monkeypatch.setattr(
        auth_deps,
        "verify_access_token",
        lambda token: {
            "sub": "auth-user-1",
            "auth_user_id": "ext-user-1",
            "phone_number": "0123456789",
            "role": "customer",
        },
    )

    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["phone_number"] == "0123456789"
