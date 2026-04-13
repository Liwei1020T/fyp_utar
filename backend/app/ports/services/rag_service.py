from __future__ import annotations

from typing import Protocol


class RagService(Protocol):
    def query(self, query: str, top_k: int) -> dict[str, object]: ...
