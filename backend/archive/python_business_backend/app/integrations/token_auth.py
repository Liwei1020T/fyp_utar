from __future__ import annotations

from typing import Any

from app.core.security import verify_access_token as verify_signed_access_token


def verify_access_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None

    return verify_signed_access_token(token)
