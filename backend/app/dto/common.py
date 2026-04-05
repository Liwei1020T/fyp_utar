from __future__ import annotations

from typing import Any
from typing import Callable
from typing import TypeVar

from app.shared.pagination import Page


T = TypeVar("T")


def page_to_dict(page: Page[T], serializer: Callable[[T], dict[str, Any]]) -> dict[str, Any]:
    return {
        "items": [serializer(item) for item in page.items],
        "total": page.total,
        "limit": page.limit,
        "offset": page.offset,
    }

