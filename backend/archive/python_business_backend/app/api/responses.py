from __future__ import annotations

from typing import Any


def success_response(*, data: Any, message: str) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def paginated_success_response(
    *,
    data: Any,
    message: str,
    total: int,
    limit: int | None,
    offset: int,
) -> dict[str, Any]:
    response = success_response(data=data, message=message)
    response["pagination"] = {
        "total": total,
        "count": len(data) if isinstance(data, list) else None,
        "limit": limit,
        "offset": offset,
    }
    return response


def error_payload(
    *,
    message: str,
    code: str,
    details: Any | None = None,
) -> dict[str, Any]:
    payload = {
        "success": False,
        "message": message,
        "error": {
            "code": code,
            "details": details or {},
        },
        # Preserve the old top-level field so the existing frontend/tests do not
        # need to switch error parsing all at once.
        "detail": message,
    }
    return payload
