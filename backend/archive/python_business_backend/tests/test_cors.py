from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_cors_preflight_allows_local_web_demo_origin():
    response = client.options(
        "/api/v1/auth/dev-login",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
