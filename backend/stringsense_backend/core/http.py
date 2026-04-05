from __future__ import annotations

from typing import Any

from app.shared.http import error_payload


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


__all__ = ["error_payload", "page_response"]
