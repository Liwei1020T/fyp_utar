from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.catalog.entities import StringItem


@dataclass(frozen=True)
class RecommendationRequestModel:
    user_id: str | None
    skill_level: str
    playing_style: str
    budget_min: float
    budget_max: float
    preferred_tension: float
    game_type: str
    frequency_per_week: int
    pref_attack: int
    pref_comfort: int
    pref_control: int
    pref_durability: int
    pref_elasticity: int
    pref_sound: int
    pref_string_movement: int
    pref_tension_retention: int
    pref_value_for_money: int
    top_n: int


@dataclass(frozen=True)
class RecommendationResultModel:
    rank: int
    string_name: str
    brand: str
    score: float
    price_rm: float | None
    aspect_scores: dict[str, float]
    reasons: list[str]
    catalog_id: str | None = None
    model_name: str | None = None
    score_breakdown: dict[str, float] | None = None
    rationale_payload: dict[str, Any] | None = None
    generated_at: datetime | None = None


@dataclass(frozen=True)
class RecommendationResponseModel:
    algorithm_version: str
    results: list[RecommendationResultModel]
    generated_at: datetime | None = None


@dataclass(frozen=True)
class RecommendationDetailModel:
    algorithm_version: str
    result: RecommendationResultModel
    generated_at: datetime | None = None


@dataclass(frozen=True)
class UserPreferenceVectorEntry:
    user_id: str
    feature_key: str
    source_layer: str
    raw_score: float | None
    preference_weight: float | None
    preferred_min: float | None
    preferred_max: float | None
    updated_at: datetime | None


@dataclass(frozen=True)
class RecommendationCandidateModel:
    item: StringItem
    matrix_by_source: dict[str, dict[str, float]]


@dataclass(frozen=True)
class CachedRecommendationRecord:
    user_id: str
    catalog_id: str
    algorithm_version: str
    preference_match_score: float | None
    rule_fit_score: float | None
    budget_fit_score: float | None
    nlp_review_score: float | None
    final_score: float
    rank_position: int
    rationale: dict[str, Any]
    generated_at: datetime | None


@dataclass(frozen=True)
class RecommendationLogRecord:
    id: str
    user_id: str | None
    phone_number: str | None
    username: str | None
    request: dict[str, Any]
    recommendation: dict[str, Any]
    algorithm_version: str
    created_at: datetime | None
