from __future__ import annotations

import subprocess
import sys

from app.config.settings import BACKEND_ROOT


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
