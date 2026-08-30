from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import CollaborativeEvidence
from app.domain.recommendation.entities import FeedbackFeatureAggregate
from app.domain.recommendation.entities import FeedbackSnapshot
from app.domain.recommendation.entities import RecommendationFeatureSignalModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.domain.recommendation.entities import RacketRecommendationContext
from app.domain.recommendation.learning_signals import CF_POLICY_VERSION
from app.domain.recommendation.learning_signals import CF_SHRINKAGE_K
from app.domain.recommendation.learning_signals import cf_weight_for_support


ALGORITHM_VERSION = "fyp1_weighted_preferences_feedback_racket_cf_v13"
PREFERENCE_SOURCE_LAYER = "profile"

CORE_RECOMMENDATION_FEATURES = (
    "repulsion",
    "control",
    "durability",
    "comfort",
    "sound",
    "elasticity",
    "tension_retention",
    "string_movement",
    "value_for_money",
)
SUPPORT_FEATURES = (
    "stability_score",
    "beginner_fit_score",
    "attacking_fit_score",
    "control_fit_score",
    "all_round_score",
)
ALL_FEATURES = CORE_RECOMMENDATION_FEATURES + SUPPORT_FEATURES

FEATURE_LABELS = {
    "repulsion": "power and rebound",
    "comfort": "comfort",
    "control": "control",
    "durability": "durability",
    "sound": "hitting sound",
    "elasticity": "elastic rebound",
    "tension_retention": "tension retention",
    "string_movement": "string movement control",
    "value_for_money": "value for money",
}

FEATURE_PRIORS = {
    "repulsion": 0.58,
    "control": 0.55,
    "durability": 0.57,
    "comfort": 0.56,
    "sound": 0.54,
    "elasticity": 0.55,
    "tension_retention": 0.54,
    "string_movement": 0.53,
    "value_for_money": 0.55,
}

FINAL_SCORE_WEIGHTS = {
    "preference_match": 0.75,
    "rule_fit": 0.15,
}
FINAL_SCORE_WEIGHT_TOTAL = sum(FINAL_SCORE_WEIGHTS.values())


@dataclass(frozen=True)
class ScoredRecommendation:
    result: RecommendationResultModel
    cache_payload: dict[str, object]
    preference_vector_rows: list[dict[str, float | str | None]]


class ContentRecommendationScorer:
    """Rule-enhanced, content-based, and explainable scorer."""

    def __init__(self, *, preference_weight_exponent: float = 1.0) -> None:
        if (
            not math.isfinite(preference_weight_exponent)
            or preference_weight_exponent <= 0
        ):
            raise ValueError("preference_weight_exponent must be positive and finite")
        self.preference_weight_exponent = preference_weight_exponent

    def build_preference_vector(
        self,
        *,
        user_id: str,
        request: RecommendationRequestModel,
    ) -> list[dict[str, float | str | None]]:
        raw_scores = {
            "repulsion": float(request.pref_attack),
            "control": float(request.pref_control),
            "durability": float(request.pref_durability),
            "comfort": float(request.pref_comfort),
            "sound": float(request.pref_sound),
            "elasticity": float(request.pref_elasticity),
            "tension_retention": float(request.pref_tension_retention),
            "string_movement": float(request.pref_string_movement),
            "value_for_money": float(request.pref_value_for_money),
        }
        adjusted_scores = {
            feature_key: raw_score**self.preference_weight_exponent
            for feature_key, raw_score in raw_scores.items()
        }
        total_weight = sum(adjusted_scores.values()) or 1.0
        return [
            {
                "feature_key": feature_key,
                "raw_score": raw_score,
                "preference_weight": round(
                    adjusted_scores[feature_key] / total_weight,
                    4,
                ),
                "preferred_min": None,
                "preferred_max": None,
            }
            for feature_key, raw_score in raw_scores.items()
        ]

    def score_candidates(
        self,
        *,
        candidates: list[RecommendationCandidateModel],
        request: RecommendationRequestModel,
        top_n: int,
        feedback_snapshot: FeedbackSnapshot | None = None,
        cf_evidence: CollaborativeEvidence | None = None,
        racket_context: RacketRecommendationContext | None = None,
    ) -> list[ScoredRecommendation]:
        preference_vector_rows = self.build_preference_vector(
            user_id=request.user_id or "",
            request=request,
        )

        scored: list[ScoredRecommendation] = []
        for candidate in candidates:
            effective_scores, feature_sources, feature_meta = _effective_item_features(
                candidate
            )
            effective_scores, feature_sources, feature_meta = _apply_feedback(
                effective_scores=effective_scores,
                feature_sources=feature_sources,
                feature_meta=feature_meta,
                aggregates=(
                    feedback_snapshot.by_catalog.get(candidate.item.id, {})
                    if feedback_snapshot is not None
                    else {}
                ),
            )
            feature_evidence = _build_feature_evidence(
                effective_scores=effective_scores,
                feature_sources=feature_sources,
                feature_meta=feature_meta,
                preference_rows=preference_vector_rows,
            )
            auxiliary_scores = _auxiliary_scores(candidate)
            preference_match = _preference_match_score(
                effective_scores=effective_scores,
                preference_rows=preference_vector_rows,
            )
            nlp_review_score = _nlp_review_alignment_score(
                feature_evidence=feature_evidence,
                preference_rows=preference_vector_rows,
            )
            rule_fit, rule_reasons, rule_events = _rule_fit_score(
                item=candidate.item,
                effective_scores=effective_scores,
                request=request,
            )
            base_score = round(
                clamp01(
                    (preference_match * FINAL_SCORE_WEIGHTS["preference_match"])
                    + (rule_fit * FINAL_SCORE_WEIGHTS["rule_fit"])
                )
                / FINAL_SCORE_WEIGHT_TOTAL,
                4,
            )
            final_score, cf_payload = _apply_cf(
                base_score=base_score,
                evidence=cf_evidence,
                catalog_id=candidate.item.id,
            )

            reasons = _build_reasons(
                request=request,
                effective_scores=effective_scores,
                preference_rows=preference_vector_rows,
                rule_reasons=rule_reasons,
            )
            breakdown = {
                "preference_match": round(preference_match, 4),
                "rule_fit": round(rule_fit, 4),
                "value_for_money": round(effective_scores["value_for_money"], 4),
                "base_score": base_score,
                "final_score": final_score,
            }
            if nlp_review_score is not None:
                breakdown["nlp_review_score"] = round(nlp_review_score, 4)

            fit_angle = _primary_fit_angle(
                effective_scores,
                request,
            )
            rationale_payload = {
                "catalog_id": candidate.item.id,
                "display_name": candidate.item.display_name,
                "brand": candidate.item.brand,
                "model_name": candidate.item.model_name,
                "algorithm_family": "feedback_calibrated_racket_cf",
                "collaborative_filtering_used": cf_payload.get("mode") == "enabled",
                "feedback_calibration_used": any(
                    (_to_float(row.get("feedback_weight")) or 0) > 0
                    for row in feature_evidence
                ),
                "feedback_snapshot_version": (
                    feedback_snapshot.snapshot_version
                    if feedback_snapshot is not None
                    else None
                ),
                "racket_context": (
                    {
                        "racket_id": racket_context.racket_id,
                        "brand": racket_context.brand,
                        "model": racket_context.model,
                        "normalized_model_key": racket_context.model_key,
                        "target_tension": racket_context.target_tension,
                    }
                    if racket_context is not None
                    else None
                ),
                "cf_shadow": cf_payload,
                "primary_fit_angle": fit_angle,
                "trade_off_summary": _trade_off_summary(
                    effective_scores,
                    breakdown,
                    request,
                ),
                "top_reasons": reasons,
                "score_breakdown": breakdown,
                "feature_sources": feature_sources,
                "feature_evidence": feature_evidence,
                "effective_feature_scores": {
                    key: round(value, 4) for key, value in effective_scores.items()
                },
                "fused_feature_scores": {
                    key: round(value, 4) for key, value in effective_scores.items()
                },
                "auxiliary_scores": {
                    key: round(value, 4) for key, value in auxiliary_scores.items()
                },
                "user_preference_vector": [
                    {
                        "feature_key": str(row["feature_key"]),
                        "raw_score": row.get("raw_score"),
                        "preference_weight": row.get("preference_weight"),
                    }
                    for row in preference_vector_rows
                ],
                "nlp_review_scores": {
                    key: round(score, 4)
                    for key, value in candidate.matrix_by_source.get(
                        "nlp_review", {}
                    ).items()
                    if (score := _signal_score(value)) is not None
                },
                "nlp_review_signal_count": sum(
                    [
                        1
                        for row in feature_evidence
                        if (_to_float(row.get("nlp_influence")) or 0) > 0
                    ]
                ),
                "nlp_review_summary": _nlp_review_summary(feature_evidence),
                "price_rm": candidate.item.price_rm,
                "rule_events": rule_events,
                "profile_context": {
                    "skill_level": request.skill_level,
                    "playing_style": request.playing_style,
                    "preferred_tension": request.preferred_tension,
                    "frequency_per_week": request.frequency_per_week,
                    "preferred_feel": request.preferred_feel,
                    "preferred_gauge": request.preferred_gauge,
                    "recent_goal": request.recent_goal,
                },
            }
            result = RecommendationResultModel(
                rank=0,
                string_name=candidate.item.display_name,
                brand=candidate.item.brand,
                model_name=candidate.item.model_name,
                catalog_id=candidate.item.id,
                score=final_score,
                price_rm=candidate.item.price_rm,
                aspect_scores={
                    feature_key: round(
                        effective_scores.get(feature_key, FEATURE_PRIORS[feature_key]),
                        4,
                    )
                    for feature_key in CORE_RECOMMENDATION_FEATURES
                },
                reasons=reasons,
                score_breakdown=breakdown,
                rationale_payload=rationale_payload,
            )
            scored.append(
                ScoredRecommendation(
                    result=result,
                    cache_payload={
                        "catalog_id": candidate.item.id,
                        "preference_match_score": breakdown["preference_match"],
                        "rule_fit_score": breakdown["rule_fit"],
                        "value_for_money_score": breakdown["value_for_money"],
                        "nlp_review_score": breakdown.get("nlp_review_score"),
                        "collaborative_score": (
                            cf_evidence.score_by_catalog.get(candidate.item.id)
                            if cf_evidence is not None
                            else None
                        ),
                        "final_score": final_score,
                        "rank_position": 0,
                        "rationale": rationale_payload,
                    },
                    preference_vector_rows=preference_vector_rows,
                )
            )

        ranked = sorted(
            scored,
            key=lambda item: (
                -item.result.score,
                item.result.brand,
                item.result.model_name or item.result.string_name,
            ),
        )
        final_ranked: list[ScoredRecommendation] = []
        for index, entry in enumerate(ranked[:top_n], start=1):
            final_ranked.append(
                ScoredRecommendation(
                    result=RecommendationResultModel(
                        rank=index,
                        string_name=entry.result.string_name,
                        brand=entry.result.brand,
                        score=entry.result.score,
                        price_rm=entry.result.price_rm,
                        aspect_scores=entry.result.aspect_scores,
                        reasons=entry.result.reasons,
                        catalog_id=entry.result.catalog_id,
                        model_name=entry.result.model_name,
                        score_breakdown=entry.result.score_breakdown,
                        rationale_payload=entry.result.rationale_payload,
                        generated_at=entry.result.generated_at,
                    ),
                    cache_payload={
                        **entry.cache_payload,
                        "rank_position": index,
                    },
                    preference_vector_rows=entry.preference_vector_rows,
                )
            )
        return final_ranked


def _effective_item_features(
    candidate: RecommendationCandidateModel,
) -> tuple[dict[str, float], dict[str, str], dict[str, dict[str, object]]]:
    official_scores = _official_feature_scores(candidate.item)
    nlp_scores = candidate.matrix_by_source.get("nlp_review", {})
    nlp_feature_signals = {
        feature_key: _nlp_feature_signal(nlp_scores, feature_key)
        for feature_key in CORE_RECOMMENDATION_FEATURES
    }

    effective: dict[str, float] = {}
    sources: dict[str, str] = {}
    feature_meta: dict[str, dict[str, object]] = {}

    for feature_key in CORE_RECOMMENDATION_FEATURES:
        prior_score = FEATURE_PRIORS[feature_key]
        official_value = official_scores.get(feature_key)
        nlp_signal = nlp_feature_signals.get(feature_key)
        nlp_value = _signal_score(nlp_signal) if nlp_signal is not None else None
        nlp_influence = 0.0
        fused_base = prior_score

        if official_value is not None and nlp_value is not None:
            source = "official_performance+nlp_review"
            fused_base = (official_value + nlp_value) / 2
            nlp_influence = 0.5
        elif official_value is not None:
            source = "official_performance"
            fused_base = official_value
        elif nlp_value is not None:
            source = "nlp_review"
            fused_base = nlp_value
            nlp_influence = 1.0
        else:
            source = "prior_fallback"

        effective[feature_key] = clamp01(fused_base)
        sources[feature_key] = source
        feature_meta[feature_key] = {
            "official_score": official_value,
            "nlp_review_score": nlp_value,
            "nlp_influence": nlp_influence,
            "prior_score": prior_score,
        }

    return effective, sources, feature_meta


def _apply_feedback(
    *,
    effective_scores: dict[str, float],
    feature_sources: dict[str, str],
    feature_meta: dict[str, dict[str, object]],
    aggregates: Mapping[str, FeedbackFeatureAggregate],
) -> tuple[dict[str, float], dict[str, str], dict[str, dict[str, object]]]:
    calibrated = dict(effective_scores)
    sources = dict(feature_sources)
    meta = {feature: dict(values) for feature, values in feature_meta.items()}
    for feature, aggregate in aggregates.items():
        if feature not in calibrated or aggregate.weight <= 0:
            continue
        baseline = calibrated[feature]
        calibrated[feature] = clamp01(
            baseline * (1 - aggregate.weight)
            + aggregate.normalized_score * aggregate.weight
        )
        sources[feature] = f"{sources[feature]}+feedback_signal"
        meta[feature].update(
            {
                "baseline_score": baseline,
                "feedback_score": aggregate.normalized_score,
                "feedback_distinct_users": aggregate.distinct_users,
                "feedback_booking_count": aggregate.booking_count,
                "feedback_confidence": aggregate.confidence,
                "feedback_weight": aggregate.weight,
                "feedback_evidence_scope": aggregate.evidence_scope,
                "feedback_racket_model_key": aggregate.racket_model_key,
                "feedback_source_version": aggregate.source_version,
            }
        )
    return calibrated, sources, meta


def _apply_cf(
    *,
    base_score: float,
    evidence: CollaborativeEvidence | None,
    catalog_id: str,
) -> tuple[float, dict[str, object]]:
    if evidence is None:
        return base_score, {
            "mode": "unavailable",
            "raw_cf_score": None,
            "cf_weight": 0.0,
            "base_score": base_score,
            "final_score": base_score,
            "fallback_reason": "not_calculated",
        }
    raw_cf_score = evidence.score_by_catalog.get(catalog_id)
    supporting_users = evidence.supporting_users_by_catalog.get(catalog_id, 0)
    cf_weight = cf_weight_for_support(supporting_users)
    final_score = base_score
    if raw_cf_score is not None and cf_weight > 0:
        final_score = round(
            clamp01(base_score * (1 - cf_weight) + raw_cf_score * cf_weight),
            4,
        )
    fallback_reason = evidence.fallback_reason
    if raw_cf_score is None:
        fallback_reason = fallback_reason or "no_candidate_support"
    elif cf_weight == 0:
        fallback_reason = "insufficient_distinct_supporting_users"
    return final_score, {
        "mode": "enabled" if cf_weight > 0 else "fallback",
        "raw_cf_score": raw_cf_score,
        "cf_confidence": round(
            supporting_users / (supporting_users + CF_SHRINKAGE_K), 4
        )
        if supporting_users
        else 0.0,
        "cf_weight": cf_weight,
        "distinct_supporting_users": supporting_users,
        "eligible_peer_count": evidence.eligible_peer_count,
        "eligible_interaction_count": evidence.eligible_interaction_count,
        "base_score": base_score,
        "final_score": final_score,
        "fallback_reason": fallback_reason,
        "policy_version": CF_POLICY_VERSION,
        "source_version": evidence.source_version,
    }


def _official_feature_scores(item: StringItem) -> dict[str, float]:
    official = item.official_performance
    if official is None:
        return {}

    scores: dict[str, float] = {}
    if official.repulsion_power is not None:
        scores["repulsion"] = official.repulsion_power / 10
    if official.shock_absorption is not None:
        scores["comfort"] = official.shock_absorption / 10
    if official.control is not None:
        scores["control"] = official.control / 10
    if official.durability is not None:
        scores["durability"] = official.durability / 10
    if official.hitting_sound is not None:
        scores["sound"] = official.hitting_sound / 10

    return {key: clamp01(value) for key, value in scores.items()}


def _nlp_feature_signal(
    nlp_scores: Mapping[str, float | RecommendationFeatureSignalModel],
    feature_key: str,
) -> float | RecommendationFeatureSignalModel | None:
    aliases = {
        "repulsion": ("repulsion", "attack"),
        "sound": ("sound", "hitting_sound"),
    }.get(feature_key, (feature_key,))

    for alias in aliases:
        value = nlp_scores.get(alias)
        if value is not None:
            return value
    return None


def _auxiliary_scores(candidate: RecommendationCandidateModel) -> dict[str, float]:
    scores: dict[str, float] = {}
    for source_layer in ("nlp_review", "hybrid_derived", "feedback_signal"):
        for feature_key, value in candidate.matrix_by_source.get(
            source_layer, {}
        ).items():
            if feature_key in SUPPORT_FEATURES and feature_key not in scores:
                score = _signal_score(value)
                if score is not None:
                    scores[feature_key] = score
    return scores


def _build_feature_evidence(
    *,
    effective_scores: dict[str, float],
    feature_sources: dict[str, str],
    feature_meta: dict[str, dict[str, object]],
    preference_rows: list[dict[str, float | str | None]],
) -> list[dict[str, object]]:
    preference_weights = {
        str(row["feature_key"]): round(float(row.get("preference_weight") or 0), 4)
        for row in preference_rows
    }
    rows: list[dict[str, object]] = []

    for feature_key in CORE_RECOMMENDATION_FEATURES:
        meta = feature_meta.get(feature_key, {})
        row = {
            "feature_key": feature_key,
            "display_label": FEATURE_LABELS[feature_key].title(),
            "effective_score": round(
                effective_scores.get(feature_key, FEATURE_PRIORS[feature_key]),
                4,
            ),
            "preference_weight": preference_weights.get(feature_key, 0.0),
            "source": feature_sources.get(feature_key, "prior_fallback"),
            "official_score": round(_to_float(meta.get("official_score")) or 0.0, 4)
            if _to_float(meta.get("official_score")) is not None
            else None,
            "nlp_review_score": round(
                _to_float(meta.get("nlp_review_score")) or 0.0,
                4,
            )
            if _to_float(meta.get("nlp_review_score")) is not None
            else None,
            "nlp_influence": round(_to_float(meta.get("nlp_influence")) or 0.0, 4),
            "prior_score": round(_to_float(meta.get("prior_score")) or 0.0, 4),
            "baseline_score": _to_float(meta.get("baseline_score")),
            "feedback_score": _to_float(meta.get("feedback_score")),
            "feedback_distinct_users": meta.get("feedback_distinct_users"),
            "feedback_booking_count": meta.get("feedback_booking_count"),
            "feedback_confidence": _to_float(meta.get("feedback_confidence")),
            "feedback_weight": _to_float(meta.get("feedback_weight")) or 0.0,
            "feedback_evidence_scope": meta.get("feedback_evidence_scope"),
            "feedback_racket_model_key": meta.get("feedback_racket_model_key"),
            "feedback_source_version": meta.get("feedback_source_version"),
        }
        rows.append(row)

    rows.sort(
        key=lambda row: (
            -(
                (_to_float(row.get("preference_weight")) or 0)
                * (_to_float(row.get("effective_score")) or 0)
            ),
            -(_to_float(row.get("effective_score")) or 0),
        )
    )
    return rows


def _nlp_review_alignment_score(
    *,
    feature_evidence: list[dict[str, object]],
    preference_rows: list[dict[str, float | str | None]],
) -> float | None:
    total_weight = sum(
        float(row.get("preference_weight") or 0)
        for row in preference_rows
        if str(row["feature_key"]) in CORE_RECOMMENDATION_FEATURES
    )
    if total_weight <= 0:
        return None

    weighted_signal = 0.0
    influence_weight = 0.0
    for row in feature_evidence:
        nlp_score = _to_float(row.get("nlp_review_score"))
        nlp_influence = _to_float(row.get("nlp_influence")) or 0
        preference_weight = _to_float(row.get("preference_weight")) or 0
        if nlp_score is None or nlp_influence <= 0:
            continue
        weighted_signal += nlp_score * preference_weight * nlp_influence
        influence_weight += preference_weight * nlp_influence

    if influence_weight <= 0:
        return None
    return clamp01(weighted_signal / influence_weight)


def _nlp_review_summary(feature_evidence: list[dict[str, object]]) -> str | None:
    backed_rows = [
        row
        for row in feature_evidence
        if _to_float(row.get("nlp_review_score")) is not None
        and (_to_float(row.get("nlp_influence")) or 0) > 0
    ]
    if not backed_rows:
        return None

    ranked = sorted(
        backed_rows,
        key=lambda row: (
            -(
                (_to_float(row.get("preference_weight")) or 0)
                * (_to_float(row.get("nlp_influence")) or 0)
                * (_to_float(row.get("nlp_review_score")) or 0)
            ),
            -(_to_float(row.get("nlp_review_score")) or 0),
        ),
    )
    labels = [
        str(row.get("display_label") or row.get("feature_key")).lower()
        for row in ranked[:2]
    ]
    if len(labels) == 1:
        return f"Review-derived signals mainly reinforce {labels[0]} for this profile."
    return (
        f"Review-derived signals reinforce {labels[0]} and {labels[1]} "
        "for this profile."
    )


def _preference_match_score(
    *,
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
) -> float:
    preference_weights: dict[str, float] = {
        str(row["feature_key"]): float(row.get("preference_weight") or 0)
        for row in preference_rows
        if str(row["feature_key"]) in CORE_RECOMMENDATION_FEATURES
    }
    total_weight = sum(preference_weights.values())
    if total_weight <= 0:
        return 0.5

    weighted_score = sum(
        weight * clamp01(effective_scores.get(feature_key, FEATURE_PRIORS[feature_key]))
        for feature_key, weight in preference_weights.items()
    )
    return clamp01(weighted_score / total_weight)


def _rule_fit_score(
    *,
    item: StringItem,
    effective_scores: dict[str, float],
    request: RecommendationRequestModel,
) -> tuple[float, list[str], list[dict[str, object]]]:
    score = 0.55
    reasons: list[str] = []
    events: list[dict[str, object]] = []

    def apply(delta: float, reason: str, rule_key: str) -> None:
        nonlocal score
        score = clamp01(score + delta)
        reasons.append(reason)
        events.append({"rule": rule_key, "delta": round(delta, 4), "reason": reason})

    gauge = item.gauge_main_mm or 0.66
    durability = effective_scores["durability"]
    comfort = effective_scores["comfort"]
    control = effective_scores["control"]
    repulsion = effective_scores["repulsion"]
    elasticity = effective_scores["elasticity"]
    tension_retention = effective_scores["tension_retention"]
    string_movement = effective_scores["string_movement"]
    gauge_category = _gauge_category(gauge)
    requested_gauge = (
        None
        if request.preferred_gauge != "no_preference"
        else "thick"
        if request.preferred_tension >= 27 or request.frequency_per_week >= 3
        else "thin"
        if request.skill_level == "beginner"
        else None
    )
    if requested_gauge == gauge_category:
        apply(
            0.07,
            f"matches the {requested_gauge} gauge suggested by your setup",
            f"setup_{requested_gauge}_gauge_bonus",
        )
    elif requested_gauge is not None:
        apply(
            -0.04,
            f"uses {gauge_category} gauge instead of the suggested {requested_gauge} gauge",
            f"setup_{requested_gauge}_gauge_penalty",
        )

    if request.preferred_gauge != "no_preference":
        if request.preferred_gauge == gauge_category:
            apply(
                0.12,
                f"matches your preferred {gauge_category} gauge",
                "preferred_gauge_bonus",
            )
        else:
            apply(
                -0.07,
                f"does not exactly match your preferred {request.preferred_gauge} gauge",
                "preferred_gauge_penalty",
            )

    feel_category = _feel_category(item)
    if request.preferred_feel == feel_category:
        apply(
            0.10,
            f"matches your preferred {feel_category} impact feel",
            "preferred_feel_bonus",
        )
    else:
        apply(
            -0.05,
            f"has a {feel_category} feel instead of your preferred {request.preferred_feel} feel",
            "preferred_feel_penalty",
        )

    if request.skill_level == "beginner":
        if ((comfort + durability) / 2) >= 0.65:
            apply(
                0.06,
                "rewards beginner-friendly comfort and durability",
                "beginner_comfort_durability_bonus",
            )

    if request.frequency_per_week >= 3:
        if durability < 0.50:
            apply(
                -0.08,
                "penalizes low durability for frequent play",
                "frequent_play_low_durability_penalty",
            )
        elif durability >= 0.68:
            apply(
                0.05,
                "supports frequent play with stronger durability",
                "frequent_play_durability_bonus",
            )

    if request.preferred_tension >= 27:
        if tension_retention >= 0.68:
            apply(
                0.06,
                "supports high preferred tension with stronger retention",
                "high_tension_retention_bonus",
            )
        elif tension_retention < 0.55:
            apply(
                -0.06,
                "penalizes lower retention for high preferred tension",
                "high_tension_retention_penalty",
            )

    if request.preferred_tension <= 23 and comfort >= 0.66:
        apply(
            0.04,
            "aligns lower-tension setup with comfort support",
            "low_tension_comfort_bonus",
        )

    if request.playing_style == "attacking":
        attack_support = (repulsion * 0.6) + (elasticity * 0.4)
        if attack_support >= 0.72:
            apply(
                0.07,
                "supports attacking play through repulsion and elasticity",
                "attacking_repulsion_elasticity_bonus",
            )
        elif repulsion < 0.55:
            apply(
                -0.05,
                "penalizes weaker repulsion for attacking style",
                "attacking_low_repulsion_penalty",
            )

    if request.playing_style == "control_defensive":
        control_support = (control * 0.55) + (string_movement * 0.45)
        if control_support >= 0.68:
            apply(
                0.07,
                "supports control style through stable response and movement control",
                "control_stability_bonus",
            )
        elif string_movement < 0.50:
            apply(
                -0.05,
                "penalizes unstable string movement for control style",
                "control_unstable_movement_penalty",
            )

    if request.playing_style == "balanced":
        all_round = (
            repulsion
            + control
            + durability
            + comfort
            + elasticity
            + tension_retention
            + string_movement
        ) / 7
        if all_round >= 0.66:
            apply(
                0.05,
                "rewards balanced all-round response",
                "balanced_all_round_bonus",
            )

    goal_feature = {
        "power": "repulsion",
        "control": "control",
        "durability": "durability",
        "comfort": "comfort",
        "tension_retention": "tension_retention",
        "value_for_money": "value_for_money",
    }.get(request.recent_goal)
    if goal_feature is not None:
        goal_score = effective_scores[goal_feature]
        goal_delta = max(-0.05, min(0.10, (goal_score - 0.55) * 0.3))
        goal_fit = goal_delta >= 0
        apply(
            goal_delta,
            (
                f"supports your recent {request.recent_goal.replace('_', ' ')} goal"
                if goal_fit
                else f"is weaker for your recent {request.recent_goal.replace('_', ' ')} goal"
            ),
            f"recent_goal_{request.recent_goal}_{'bonus' if goal_fit else 'penalty'}",
        )
    elif request.recent_goal == "balanced":
        balanced_score = sum(effective_scores.values()) / len(effective_scores)
        if balanced_score >= 0.64:
            apply(
                0.04,
                "supports your recent balanced setup goal",
                "recent_goal_balanced_bonus",
            )

    return score, reasons, events


def _gauge_category(gauge_mm: float) -> str:
    if gauge_mm <= 0.64:
        return "thin"
    if gauge_mm <= 0.67:
        return "medium"
    return "thick"


def _feel_category(item: StringItem) -> str:
    feel = item.official_performance.feel if item.official_performance else None
    if feel is None:
        return "medium"
    if feel <= 4:
        return "soft"
    if feel <= 6.5:
        return "medium"
    return "hard"


def _build_reasons(
    *,
    request: RecommendationRequestModel,
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
    rule_reasons: list[str],
) -> list[str]:
    reasons: list[str] = []

    for feature_key, label in _top_weighted_preference_reasons(
        effective_scores,
        preference_rows,
    ):
        reasons.append(f"matches your {label} priority")

    reasons.extend(rule_reasons)

    if request.playing_style == "attacking" and effective_scores["repulsion"] >= 0.75:
        reasons.append("strong repulsion response for attacking rallies")
    if (
        request.playing_style == "control_defensive"
        and effective_scores["control"] >= 0.75
    ):
        reasons.append("control-oriented response for placement and touch")

    return _unique(reasons)[:4]


def _top_weighted_preference_reasons(
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
) -> list[tuple[str, str]]:
    ranked = []
    for row in preference_rows:
        feature_key = str(row["feature_key"])
        if feature_key not in CORE_RECOMMENDATION_FEATURES:
            continue
        weight = float(row.get("preference_weight") or 0)
        ranked.append((weight * effective_scores.get(feature_key, 0.5), feature_key))
    ranked.sort(reverse=True)
    return [(feature_key, FEATURE_LABELS[feature_key]) for _, feature_key in ranked[:2]]


def _primary_fit_angle(
    effective_scores: dict[str, float],
    request: RecommendationRequestModel,
) -> str:
    if (
        request.recent_goal == "value_for_money"
        and effective_scores["value_for_money"] >= 0.7
    ):
        return "Value pick"
    if request.playing_style == "attacking" and effective_scores["repulsion"] >= 0.7:
        return "Attack pick"
    if (
        request.playing_style == "control_defensive"
        and effective_scores["control"] >= 0.7
    ):
        return "Control pick"

    ranked = sorted(
        (
            ("Durability pick", effective_scores["durability"]),
            ("Comfort pick", effective_scores["comfort"]),
            ("Elastic pick", effective_scores["elasticity"]),
            ("Tension-safe pick", effective_scores["tension_retention"]),
            ("Stable-bed pick", effective_scores["string_movement"]),
            ("Sound pick", effective_scores["sound"]),
            ("Value pick", effective_scores["value_for_money"]),
            ("All-round pick", sum(effective_scores.values()) / len(effective_scores)),
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[0][0]


def _trade_off_summary(
    effective_scores: dict[str, float],
    breakdown: dict[str, float],
    request: RecommendationRequestModel,
) -> str:
    weakest_component = min(
        (
            ("preference match", breakdown["preference_match"]),
            ("rule fit", breakdown["rule_fit"]),
        ),
        key=lambda item: item[1],
    )[0]

    if weakest_component == "rule fit":
        return (
            "Domain-rule support is moderate here for your "
            f"{request.playing_style.replace('_', ' ')} profile."
        )

    weakest_feature = min(effective_scores.items(), key=lambda item: item[1])[0]
    return (
        f"Lower {weakest_feature.replace('_', ' ')} is the main performance trade-off."
    )


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _signal_score(value: object) -> float | None:
    if isinstance(value, RecommendationFeatureSignalModel):
        return clamp01(value.normalized_score)
    score = _to_float(value)
    return clamp01(score) if score is not None else None


def _to_float(value: object) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
