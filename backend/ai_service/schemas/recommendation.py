from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RecommendationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    skill_level: str | None = None
    playing_style: str | None = None
    preferred_tension: float | None = Field(default=None, ge=18, le=35)
    durability_priority: int | None = Field(default=None, ge=1, le=5)
    repulsion_priority: int | None = Field(default=None, ge=1, le=5)
    control_priority: int | None = Field(default=None, ge=1, le=5)
    sound_priority: int | None = Field(default=None, ge=1, le=5)
    tension_retention_priority: int | None = Field(default=None, ge=1, le=5)


class StringCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    brand: str
    model_name: str
    price: float | None = None
    recommended_tension_min: int | None = None
    recommended_tension_max: int | None = None
    repulsion_score: float | None = None
    durability_score: float | None = None
    control_score: float | None = None
    sound_score: float | None = None
    tension_retention_score: float | None = None
    value_score: float | None = None
    feature_text: str | None = None
    feature_text_en: str | None = None


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: RecommendationContext = Field(default_factory=RecommendationContext)
    request: RecommendationContext = Field(default_factory=RecommendationContext)
    catalog: list[StringCandidate]
    top_k: int = Field(default=5, ge=1, le=20)


class RecommendationResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    id: str
    string_id: str
    brand: str
    model_name: str
    match_score: float
    short_reason: str
    price: float | None = None
    key_strengths: list[str]
    suggested_tension_range: str


class RecommendResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str
    evaluated_candidates: int
    results: list[RecommendationResultItem]


class ExplainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: RecommendationContext = Field(default_factory=RecommendationContext)
    request: RecommendationContext = Field(default_factory=RecommendationContext)
    string: StringCandidate


class ExplainResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str
    summary: str
    evidence: list[str]
    key_strengths: list[str]
