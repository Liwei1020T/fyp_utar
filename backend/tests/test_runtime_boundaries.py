from __future__ import annotations

import ast
import re

from fastapi.testclient import TestClient

from app.config.settings import BACKEND_ROOT
from app.main import app


REMOVED_API_OPERATIONS = {
    ("DELETE", "/api/admin/strings/{string_id}"),
    ("GET", "/api/admin/inventory/strings/{string_id}/movements"),
    ("GET", "/api/admin/device-tokens"),
    ("GET", "/api/admin/recommendations/logs"),
    ("GET", "/api/admin/slots"),
    ("GET", "/api/admin/strings"),
    ("GET", "/api/rackets/{racket_id}/history"),
    ("GET", "/api/strings/{string_id}"),
    ("POST", "/api/admin/strings"),
    ("POST", "/api/auth/delete-account-request"),
    ("POST", "/api/devices/push-token"),
    ("POST", "/api/recommendations/preview"),
    ("POST", "/api/recommendations/profile"),
    ("PUT", "/api/admin/strings/{string_id}"),
    ("PUT", "/api/admin/strings/{string_id}/official-performance"),
}
client = TestClient(app)


def test_api_responses_include_security_headers() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == (
        "camera=(), geolocation=(), microphone=()"
    )


def test_use_cases_do_not_import_adapters_or_runtime_config() -> None:
    violations: list[str] = []
    for path in (BACKEND_ROOT / "app" / "use_cases").rglob("*.py"):
        if path.name.startswith("._"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (
                (node.module or "").startswith("app.adapters")
                or (node.module or "").startswith("app.config")
            ):
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno}")
    assert not violations, violations


def test_mobile_api_paths_exist_in_backend_openapi() -> None:
    # ponytail: source-string route check; generate a typed client if schema-level
    # request/response compatibility becomes necessary.
    source = (BACKEND_ROOT.parent / "mobile" / "services" / "backendApi.ts").read_text(
        encoding="utf-8"
    )
    mobile_paths = {
        _normalize_route(path)
        for _, path in re.findall(r"([`'\"])(/[a-z][^`'\"\s]*)", source)
        if not path.startswith("//")
    }
    backend_paths = {
        _normalize_route(path.removeprefix("/api")) for path in app.openapi()["paths"]
    }

    assert mobile_paths <= backend_paths, sorted(mobile_paths - backend_paths)


def test_removed_api_operations_stay_absent() -> None:
    active_operations = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
    }

    assert REMOVED_API_OPERATIONS.isdisjoint(active_operations)


def _normalize_route(path: str) -> str:
    path = path.split("?", 1)[0].replace("${suffix}", "")
    return re.sub(r"\$\{[^}]+\}|\{[^}]+\}", "{parameter}", path)
