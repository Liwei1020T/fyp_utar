from __future__ import annotations

from typing import Any


def page_response(
    *,
    items: list[Any],
    total: int,
    limit: int | None,
    offset: int,
) -> dict[str, Any]:
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def error_payload(
    *,
    code: str,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }
