from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from datetime import timezone

from app.domain.recommendation.entities import CollaborativeEvidence
from app.domain.recommendation.entities import CommunityFeatureAggregate
from app.domain.recommendation.entities import CommunityFeedbackRow
from app.domain.recommendation.entities import CommunitySnapshot
from app.domain.recommendation.entities import RecommendationInteraction


COMMUNITY_POLICY_VERSION = "community_feedback_v3_no_durability_provenance"
COMMUNITY_SHRINKAGE_K = 10
COMMUNITY_MAX_WEIGHT = 0.30
COMMUNITY_FEATURES = ("comfort", "control", "repulsion")
CF_POLICY_VERSION = "racket_cf_enabled_v11_v1"
CF_SHRINKAGE_K = 10
CF_MAX_WEIGHT = 0.20
CF_MIN_SUPPORTING_USERS = 3
TENSION_SIMILARITY_WINDOW_LBS = 4.0

STANDARD_RACKET_MODELS: tuple[tuple[str, str, str], ...] = (
    ("li ning:axforce 80", "Li-Ning", "Axforce 80"),
    ("victor:auraspeed 90k ii", "Victor", "Auraspeed 90K II"),
    ("victor:thruster ryuga ii", "Victor", "Thruster Ryuga II"),
    ("yonex:arcsaber 11 pro", "Yonex", "Arcsaber 11 Pro"),
    ("yonex:astrox 88d pro", "Yonex", "Astrox 88D Pro"),
    ("yonex:nanoflare 1000 z", "Yonex", "Nanoflare 1000 Z"),
)
_STANDARD_RACKET_MODELS_BY_KEY = {
    key: (brand, model) for key, brand, model in STANDARD_RACKET_MODELS
}


def normalize_racket_model_key(brand: str | None, model: str | None) -> str | None:
    normalized_brand = _normalize_identity_part(brand)
    normalized_model = _normalize_identity_part(model)
    if not normalized_brand or not normalized_model:
        return None
    return f"{normalized_brand}:{normalized_model}"


def standard_racket_model_for_key(model_key: str) -> tuple[str, str] | None:
    return _STANDARD_RACKET_MODELS_BY_KEY.get(model_key)


def canonical_racket_model_key(
    brand: str | None,
    model: str | None,
) -> str | None:
    model_key = normalize_racket_model_key(brand, model)
    return model_key if model_key in _STANDARD_RACKET_MODELS_BY_KEY else None


def cf_weight_for_support(distinct_supporting_users: int) -> float:
    if distinct_supporting_users < CF_MIN_SUPPORTING_USERS:
        return 0.0
    confidence = distinct_supporting_users / (
        distinct_supporting_users + CF_SHRINKAGE_K
    )
    return round(CF_MAX_WEIGHT * confidence, 4)


def build_community_snapshot(
    rows: Iterable[CommunityFeedbackRow],
    *,
    target_racket_model_key: str | None,
) -> CommunitySnapshot:
    eligible = _eligible_feedback_values(rows)
    global_buckets: dict[tuple[str, str, str], list[tuple[int, str]]] = defaultdict(
        list
    )
    context_buckets: dict[tuple[str, str, str], list[tuple[int, str]]] = defaultdict(
        list
    )
    canonical: list[dict[str, object]] = []

    for row, feature, rating in eligible:
        global_buckets[(row.catalog_id, feature, row.user_id)].append(
            (rating, row.feedback_id)
        )
        if (
            target_racket_model_key is not None
            and row.racket_model_key == target_racket_model_key
        ):
            context_buckets[(row.catalog_id, feature, row.user_id)].append(
                (rating, row.feedback_id)
            )
        canonical.append(
            {
                "feedback_id": row.feedback_id,
                "catalog_id": row.catalog_id,
                "feature": feature,
                "rating": rating,
                "racket_model_key": row.racket_model_key,
            }
        )

    global_aggregates = _aggregate_feedback_buckets(
        global_buckets,
        evidence_scope="global_string",
        racket_model_key=None,
    )
    context_aggregates = _aggregate_feedback_buckets(
        context_buckets,
        evidence_scope="exact_racket_model",
        racket_model_key=target_racket_model_key,
    )

    selected: dict[str, dict[str, CommunityFeatureAggregate]] = defaultdict(dict)
    keys = set(global_aggregates) | set(context_aggregates)
    for catalog_id, feature in keys:
        selected[catalog_id][feature] = (
            context_aggregates.get((catalog_id, feature))
            or global_aggregates[(catalog_id, feature)]
        )

    return CommunitySnapshot(
        by_catalog={
            catalog_id: dict(features) for catalog_id, features in selected.items()
        },
        snapshot_version=_digest(COMMUNITY_POLICY_VERSION, canonical),
    )


def build_cf_evidence(
    interactions: Iterable[RecommendationInteraction],
    *,
    current_user_id: str,
    current_preference_vector: tuple[int, ...],
    target_racket_model_key: str | None,
    target_tension: float,
) -> CollaborativeEvidence:
    rows = sorted(
        interactions,
        key=lambda item: (item.booking_id, item.user_id, item.catalog_id),
    )
    source_version = _digest(
        CF_POLICY_VERSION,
        [
            {
                "booking_id": row.booking_id,
                "user_id": row.user_id,
                "catalog_id": row.catalog_id,
                "racket_model_key": row.racket_model_key,
                "requested_tension": row.requested_tension,
                "completed_at": row.completed_at.astimezone(timezone.utc).isoformat(),
            }
            for row in rows
        ],
    )
    if target_racket_model_key is None:
        return _empty_cf(source_version, len(rows), "no_racket_selected")

    peer_rows = [
        row
        for row in rows
        if row.user_id != current_user_id
        and row.racket_model_key == target_racket_model_key
        and row.requested_tension is not None
        and all(value is not None for value in row.preference_vector)
    ]
    if not peer_rows:
        return _empty_cf(source_version, len(rows), "no_exact_model_peers")

    peer_vectors = {
        row.user_id: tuple(
            int(value) for value in row.preference_vector if value is not None
        )
        for row in peer_rows
    }
    peer_weights = {
        user_id: _cosine_similarity(current_preference_vector, vector)
        for user_id, vector in peer_vectors.items()
    }
    denominator = sum(peer_weights.values())
    if denominator <= 0:
        return _empty_cf(source_version, len(rows), "no_similar_peers")

    candidate_support: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in peer_rows:
        assert row.requested_tension is not None
        candidate_support[(row.user_id, row.catalog_id)].append(
            max(
                0.0,
                1.0
                - abs(target_tension - row.requested_tension)
                / TENSION_SIMILARITY_WINDOW_LBS,
            )
        )

    score_by_catalog: dict[str, float] = {}
    supporting_users_by_catalog: dict[str, int] = {}
    catalog_ids = {catalog_id for _, catalog_id in candidate_support}
    for catalog_id in catalog_ids:
        support = [
            (user_id, sum(values) / len(values))
            for (user_id, candidate_id), values in candidate_support.items()
            if candidate_id == catalog_id
        ]
        numerator = sum(
            peer_weights[user_id] * tension_fit for user_id, tension_fit in support
        )
        score_by_catalog[catalog_id] = round(numerator / denominator, 4)
        supporting_users_by_catalog[catalog_id] = sum(
            1 for _, tension_fit in support if tension_fit > 0
        )

    return CollaborativeEvidence(
        score_by_catalog=score_by_catalog,
        supporting_users_by_catalog=supporting_users_by_catalog,
        source_version=source_version,
        eligible_interaction_count=len(rows),
        eligible_peer_count=len(peer_weights),
        fallback_reason=None if score_by_catalog else "no_tension_supported_candidates",
    )


def _eligible_feedback_values(
    rows: Iterable[CommunityFeedbackRow],
) -> list[tuple[CommunityFeedbackRow, str, int]]:
    eligible: list[tuple[CommunityFeedbackRow, str, int]] = []
    for row in rows:
        for feature in COMMUNITY_FEATURES:
            rating = row.ratings.get(feature)
            if rating is None or not 1 <= rating <= 5:
                continue
            eligible.append((row, feature, rating))
    return eligible


def _aggregate_feedback_buckets(
    buckets: dict[tuple[str, str, str], list[tuple[int, str]]],
    *,
    evidence_scope: str,
    racket_model_key: str | None,
) -> dict[tuple[str, str], CommunityFeatureAggregate]:
    grouped_users: dict[tuple[str, str], list[tuple[float, list[tuple[int, str]]]]] = (
        defaultdict(list)
    )
    for (catalog_id, feature, _user_id), values in buckets.items():
        grouped_users[(catalog_id, feature)].append(
            (
                sum(rating for rating, _ in values) / len(values),
                sorted(values, key=lambda value: (value[1], value[0])),
            )
        )

    aggregates: dict[tuple[str, str], CommunityFeatureAggregate] = {}
    for key, users in grouped_users.items():
        distinct_users = len(users)
        normalized_score = ((sum(value for value, _ in users) / distinct_users) - 1) / 4
        confidence = distinct_users / (distinct_users + COMMUNITY_SHRINKAGE_K)
        canonical = sorted(values for _, values in users)
        aggregates[key] = CommunityFeatureAggregate(
            normalized_score=round(normalized_score, 4),
            distinct_users=distinct_users,
            booking_count=sum(len(values) for _, values in users),
            confidence=round(confidence, 4),
            weight=round(COMMUNITY_MAX_WEIGHT * confidence, 4),
            evidence_scope=evidence_scope,
            racket_model_key=racket_model_key,
            source_version=_digest(
                COMMUNITY_POLICY_VERSION,
                [
                    {
                        "key": key,
                        "feedback_values": canonical,
                        "scope": evidence_scope,
                    }
                ],
            ),
        )
    return aggregates


def _normalize_identity_part(value: str | None) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return " ".join(
        "".join(
            character if character.isalnum() else " " for character in normalized
        ).split()
    )


def _cosine_similarity(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
        sum(value * value for value in right)
    )
    return numerator / denominator if denominator else 0.0


def _digest(policy: str, rows: list[dict[str, object]]) -> str:
    rows = sorted(
        rows,
        key=lambda row: json.dumps(
            row,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ),
    )
    payload = json.dumps(
        {"policy": policy, "rows": rows},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _empty_cf(
    source_version: str,
    eligible_interaction_count: int,
    reason: str,
) -> CollaborativeEvidence:
    return CollaborativeEvidence(
        score_by_catalog={},
        supporting_users_by_catalog={},
        source_version=source_version,
        eligible_interaction_count=eligible_interaction_count,
        eligible_peer_count=0,
        fallback_reason=reason,
    )
