from __future__ import annotations

from dataclasses import dataclass
from typing import Generic
from typing import TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    limit: int | None
    offset: int
