from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections.abc import Mapping
from typing import Any

from app.domain.catalog.entities import StringItem


@dataclass(frozen=True)
class RecommendationRequestModel:
    user_id: str | None
    skill_level: str
    playing_style: str
    preferred_tension: float
    frequency_per_week: int
    preferred_feel: str
    preferred_gauge: str
    recent_goal: str
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
    run_id: str | None = None
    generated_at: datetime | None = None


@dataclass(frozen=True)
class RecommendationDetailModel:
    algorithm_version: str
    result: RecommendationResultModel
    run_id: str | None = None
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
class RecommendationFeatureSignalModel:
    normalized_score: float
    raw_value: float | None = None
    evidence_note: str | None = None


@dataclass(frozen=True)
class RecommendationCandidateModel:
    item: StringItem
    matrix_by_source: Mapping[
        str,
        Mapping[str, float | RecommendationFeatureSignalModel],
    ]


@dataclass(frozen=True)
class RacketRecommendationContext:
    racket_id: str
    brand: str
    model: str
    model_key: str | None
    target_tension: float


@dataclass(frozen=True)
class CommunityFeedbackRow:
    feedback_id: str
    user_id: str
    catalog_id: str
    racket_model_key: str | None
    ratings: Mapping[str, int | None]


@dataclass(frozen=True)
class CommunityFeatureAggregate:
    normalized_score: float
    distinct_users: int
    booking_count: int
    confidence: float
    weight: float
    evidence_scope: str
    racket_model_key: str | None
    source_version: str


@dataclass(frozen=True)
class CommunitySnapshot:
    by_catalog: Mapping[str, Mapping[str, CommunityFeatureAggregate]]
    snapshot_version: str


@dataclass(frozen=True)
class RecommendationInteraction:
    booking_id: str
    user_id: str
    catalog_id: str
    racket_id: str | None
    racket_model_key: str
    requested_tension: float | None
    completed_at: datetime
    preference_vector: tuple[int | None, ...]


@dataclass(frozen=True)
class CollaborativeEvidence:
    score_by_catalog: Mapping[str, float]
    supporting_users_by_catalog: Mapping[str, int]
    source_version: str
    eligible_interaction_count: int
    eligible_peer_count: int
    fallback_reason: str | None


@dataclass(frozen=True)
class CachedRecommendationRecord:
    user_id: str
    catalog_id: str
    algorithm_version: str
    preference_match_score: float | None
    rule_fit_score: float | None
    value_for_money_score: float | None
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


@dataclass(frozen=True)
class RecommendationRunItemRecord:
    id: str
    catalog_id: str
    rank_position: int
    final_score: float
    preference_match_score: float | None
    rule_fit_score: float | None
    value_for_money_score: float | None
    nlp_review_score: float | None
    score_breakdown: dict[str, Any]
    rationale: dict[str, Any]


@dataclass(frozen=True)
class RecommendationRunRecord:
    id: str
    user_id: str | None
    phone_number: str | None
    username: str | None
    algorithm_version: str
    request_snapshot: dict[str, Any]
    profile_snapshot: dict[str, Any]
    generated_at: datetime | None
    items: list[RecommendationRunItemRecord]
