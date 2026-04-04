from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


SKILL_LEVELS = ("beginner", "intermediate", "advanced")
PLAYING_STYLES = ("attacking", "balanced", "control_defensive")
GAME_TYPES = ("singles", "doubles")


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    skill_level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    playing_style: str = Field(pattern="^(attacking|balanced|control_defensive)$")
    budget_min: float = Field(ge=0, le=999)
    budget_max: float = Field(ge=0, le=999)
    preferred_tension: float = Field(ge=16, le=35)
    game_type: str = Field(pattern="^(singles|doubles)$")
    frequency_per_week: int = Field(ge=0, le=14)
    pref_attack: int = Field(ge=1, le=5)
    pref_comfort: int = Field(ge=1, le=5)
    pref_control: int = Field(ge=1, le=5)
    pref_durability: int = Field(ge=1, le=5)
    pref_elasticity: int = Field(ge=1, le=5)
    pref_sound: int = Field(ge=1, le=5)
    pref_string_movement: int = Field(ge=1, le=5)
    pref_tension_retention: int = Field(ge=1, le=5)
    pref_value_for_money: int = Field(ge=1, le=5)
    top_n: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def validate_budget(self) -> "RecommendationRequest":
        if self.budget_min > self.budget_max:
            raise ValueError("budget_min must be less than or equal to budget_max")
        return self


class StringRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    brand: str
    model_name: str
    normalized_name: str
    price_rm: float | None = None
    attack: float = Field(ge=0, le=1)
    comfort: float = Field(ge=0, le=1)
    control: float = Field(ge=0, le=1)
    durability: float = Field(ge=0, le=1)
    elasticity: float = Field(ge=0, le=1)
    sound: float = Field(ge=0, le=1)
    string_movement: float = Field(ge=0, le=1)
    tension_retention: float = Field(ge=0, le=1)
    value_for_money: float = Field(ge=0, le=1)
    beginner_fit_score: float = Field(default=0.5, ge=0, le=1)
    stability_score: float = Field(default=0.5, ge=0, le=1)
    all_round_score: float = Field(default=0.5, ge=0, le=1)
    source_item_id: str | None = None
    source_url: str | None = None


class RecommendationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    string_name: str
    brand: str
    score: float
    price_rm: float | None
    aspect_scores: dict[str, float]
    reasons: list[str]


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str
    results: list[RecommendationResult]


class ExplainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    string_name: str
    user_context: RecommendationRequest


class ExplainResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str
    string_name: str
    reasons: list[str]
    aspect_scores: dict[str, float]


class ReviewAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviews: list[str]


class ReviewAspectSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aspect: str
    score: float
    evidence: list[str]


class ReviewAnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_count: int
    aspects: list[ReviewAspectSignal]


class RagQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class RagQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int
    matches: list[dict[str, Any]]
