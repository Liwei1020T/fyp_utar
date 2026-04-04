from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    rating: float | None = None
    source: str | None = None
    review_text: str = Field(min_length=1)


class ReviewAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    string_id: str | None = None
    reviews: list[ReviewRecord]


class ReviewAspectSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aspect: str
    sentiment: str
    confidence: float
    evidence: list[str]


class ReviewAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_count: int
    extracted_aspects: list[ReviewAspectSummary]
    summary: str
