from __future__ import annotations

from typing import Protocol


class ReviewAnalysisService(Protocol):
    def analyze_reviews(self, reviews: list[str]) -> dict[str, object]: ...

