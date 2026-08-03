from __future__ import annotations

import ast
import re
import subprocess
import sys

from app.config.settings import BACKEND_ROOT
from app.main import app


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


def test_unified_app_import_does_not_load_legacy_ai_runtime() -> None:
    script = """
import sys
import app.main  # noqa: F401

blocked = {
    "ai_service.service",
}
loaded = sorted(blocked.intersection(sys.modules))
if loaded:
    raise SystemExit(f"legacy AI runtime loaded: {loaded}")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


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


def _normalize_route(path: str) -> str:
    path = path.split("?", 1)[0].replace("${suffix}", "")
    return re.sub(r"\$\{[^}]+\}|\{[^}]+\}", "{parameter}", path)
