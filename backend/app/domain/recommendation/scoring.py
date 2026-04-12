from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResultModel


ALGORITHM_VERSION = "hybrid_preference_rule_budget_nlp_v1"
PREFERENCE_SOURCE_LAYER = "profile_onboarding_v1"

PRIMARY_FEATURES = (
    "attack",
    "comfort",
    "control",
    "durability",
    "elasticity",
    "sound",
    "string_movement",
    "tension_retention",
    "value_for_money",
)
DOMAIN_TO_STORAGE_FEATURE_KEY = {
    "sound": "hitting_sound",
}
STORAGE_TO_DOMAIN_FEATURE_KEY = {
    storage_key: domain_key
    for domain_key, storage_key in DOMAIN_TO_STORAGE_FEATURE_KEY.items()
}
DERIVED_FEATURES = (
    "stability_score",
    "all_round_score",
    "attacking_fit_score",
    "control_fit_score",
    "beginner_fit_score",
)
ALL_FEATURES = PRIMARY_FEATURES + DERIVED_FEATURES

COMMUNITY_TAG_EFFECTS: dict[str, dict[str, float]] = {
    "弹性好": {"attack": 0.18, "elasticity": 0.22, "sound": 0.12},
    "耐打": {"durability": 0.25, "stability_score": 0.16, "tension_retention": 0.12},
    "控球好": {"control": 0.24, "beginner_fit_score": 0.06},
    "声音清脆": {"sound": 0.26, "attack": 0.08},
    "性价比高": {"value_for_money": 0.28, "beginner_fit_score": 0.08},
    "性价比低": {"value_for_money": -0.24},
    "掉磅快": {"tension_retention": -0.26, "stability_score": -0.10},
    "手感好": {"comfort": 0.20, "control": 0.08},
    "震手": {"comfort": -0.20},
    "粘手": {"string_movement": 0.14, "control": 0.08},
}


@dataclass(frozen=True)
class ScoredRecommendation:
    result: RecommendationResultModel
    cache_payload: dict[str, object]
    preference_vector_rows: list[dict[str, float | str | None]]


class HybridRecommendationScorer:
    def build_preference_vector(
        self,
        *,
        user_id: str,
        request: RecommendationRequestModel,
    ) -> list[dict[str, float | str | None]]:
        raw_weights = {
            "attack": request.pref_attack / 5,
            "comfort": request.pref_comfort / 5,
            "control": request.pref_control / 5,
            "durability": request.pref_durability / 5,
            "elasticity": request.pref_elasticity / 5,
            "sound": request.pref_sound / 5,
            "string_movement": request.pref_string_movement / 5,
            "tension_retention": request.pref_tension_retention / 5,
            "value_for_money": request.pref_value_for_money / 5,
        }
        total_weight = sum(raw_weights.values()) or 1.0
        rows = [
            {
                "feature_key": _storage_feature_key(feature_key),
                "preference_weight": round(weight / total_weight, 4),
                "preferred_min": None,
                "preferred_max": None,
            }
            for feature_key, weight in raw_weights.items()
        ]

        gauge_min, gauge_max = _preferred_gauge_range(request)
        rows.append(
            {
                "feature_key": "gauge_mm",
                "preference_weight": 0.18,
                "preferred_min": gauge_min,
                "preferred_max": gauge_max,
            }
        )
        rows.append(
            {
                "feature_key": "price_rm",
                "preference_weight": 1.0,
                "preferred_min": round(request.budget_min, 2),
                "preferred_max": round(request.budget_max, 2),
            }
        )
        return rows

    def score_candidates(
        self,
        *,
        candidates: list[RecommendationCandidateModel],
        request: RecommendationRequestModel,
        top_n: int,
    ) -> list[ScoredRecommendation]:
        preference_vector_rows = self.build_preference_vector(
            user_id=request.user_id or "",
            request=request,
        )
        scored: list[ScoredRecommendation] = []
        for candidate in candidates:
            fused_scores, feature_sources = _fuse_item_features(candidate)
            preference_match = _preference_match_score(
                fused_scores=fused_scores,
                item=candidate.item,
                preference_rows=preference_vector_rows,
            )
            budget_fit = _budget_fit_score(candidate.item.price_rm, request)
            nlp_review_score = _nlp_review_score(
                matrix_scores=candidate.matrix_by_source.get("nlp_review", {}),
                preference_rows=preference_vector_rows,
            )
            rule_fit, rule_reasons, rule_events = _rule_fit_score(
                item=candidate.item,
                fused_scores=fused_scores,
                request=request,
            )
            final_score = round(
                clamp01(
                    (preference_match * 0.55)
                    + (rule_fit * 0.20)
                    + (budget_fit * 0.15)
                    + (nlp_review_score * 0.10)
                ),
                4,
            )

            reasons = _build_reasons(
                item=candidate.item,
                request=request,
                fused_scores=fused_scores,
                preference_rows=preference_vector_rows,
                budget_fit=budget_fit,
                rule_reasons=rule_reasons,
            )
            breakdown = {
                "preference_match": round(preference_match, 4),
                "rule_fit": round(rule_fit, 4),
                "budget_fit": round(budget_fit, 4),
                "nlp_review_score": round(nlp_review_score, 4),
                "final_score": final_score,
            }
            rationale_payload = {
                "catalog_id": candidate.item.id,
                "display_name": candidate.item.display_name,
                "brand": candidate.item.brand,
                "model_name": candidate.item.model_name,
                "top_reasons": reasons,
                "score_breakdown": breakdown,
                "feature_sources": feature_sources,
                "fused_feature_scores": {
                    key: round(value, 4) for key, value in fused_scores.items()
                },
                "nlp_review_scores": {
                    key: round(value, 4)
                    for key, value in candidate.matrix_by_source.get(
                        "nlp_review", {}
                    ).items()
                },
                "budget": {
                    "price_rm": candidate.item.price_rm,
                    "budget_min": request.budget_min,
                    "budget_max": request.budget_max,
                },
                "rule_events": rule_events,
                "profile_context": {
                    "skill_level": request.skill_level,
                    "playing_style": request.playing_style,
                    "preferred_tension": request.preferred_tension,
                    "game_type": request.game_type,
                    "frequency_per_week": request.frequency_per_week,
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
                    feature_key: round(fused_scores.get(feature_key, 0.5), 4)
                    for feature_key in PRIMARY_FEATURES
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
                        "budget_fit_score": breakdown["budget_fit"],
                        "nlp_review_score": breakdown["nlp_review_score"],
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
                item.result.price_rm
                if item.result.price_rm is not None
                else float("inf"),
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


def _fuse_item_features(
    candidate: RecommendationCandidateModel,
) -> tuple[dict[str, float], dict[str, str]]:
    official_scores = _official_feature_scores(candidate.item)
    nlp_scores = candidate.matrix_by_source.get("nlp_review", {})
    structured_scores = _structured_feature_scores(candidate.item)
    community_scores = _community_feature_scores(candidate.item)
    hybrid_scores = candidate.matrix_by_source.get("hybrid_derived", {})

    fused: dict[str, float] = {}
    sources: dict[str, str] = {}
    source_order = (
        ("official_performance", official_scores),
        ("nlp_review", nlp_scores),
        ("catalog_structured", structured_scores),
        ("community_signal", community_scores),
        ("hybrid_derived", hybrid_scores),
    )
    for feature_key in ALL_FEATURES:
        for source_name, values in source_order:
            value = values.get(feature_key)
            if value is None:
                continue
            fused[feature_key] = clamp01(value)
            sources[feature_key] = source_name
            break
        if feature_key not in fused:
            fused[feature_key] = 0.5
            sources[feature_key] = "default"
    return fused, sources


def _official_feature_scores(item: StringItem) -> dict[str, float]:
    official = item.official_performance
    if official is None:
        return {}
    scores: dict[str, float] = {}
    if official.repulsion_power is not None:
        scores["attack"] = official.repulsion_power / 10
    if official.shock_absorption is not None:
        scores["comfort"] = official.shock_absorption / 10
    if official.control is not None:
        scores["control"] = official.control / 10
    if official.durability is not None:
        scores["durability"] = official.durability / 10
    if official.hitting_sound is not None:
        scores["sound"] = official.hitting_sound / 10
    if scores:
        scores["all_round_score"] = sum(scores.values()) / len(scores)
        scores["attacking_fit_score"] = (scores.get("attack", 0.5) * 0.7) + (
            scores.get("sound", 0.5) * 0.3
        )
        scores["control_fit_score"] = (scores.get("control", 0.5) * 0.7) + (
            scores.get("comfort", 0.5) * 0.3
        )
        scores["beginner_fit_score"] = (
            (scores.get("comfort", 0.5) * 0.5)
            + (scores.get("control", 0.5) * 0.3)
            + (scores.get("durability", 0.5) * 0.2)
        )
        scores["stability_score"] = (
            (scores.get("durability", 0.5) * 0.5)
            + (scores.get("control", 0.5) * 0.3)
            + (scores.get("comfort", 0.5) * 0.2)
        )
    return {key: clamp01(value) for key, value in scores.items()}


def _structured_feature_scores(item: StringItem) -> dict[str, float]:
    gauge = item.gauge_main_mm
    if gauge is None:
        return {}
    thin_score = clamp01((0.69 - gauge) / 0.07)
    thick_score = clamp01((gauge - 0.63) / 0.07)
    mid_score = clamp01(1 - (abs(gauge - 0.66) / 0.03))
    scores = {
        "attack": 0.45 + (thin_score * 0.33),
        "comfort": 0.45 + (thick_score * 0.18),
        "control": 0.45 + (mid_score * 0.20) + (thick_score * 0.08),
        "durability": 0.42 + (thick_score * 0.38),
        "elasticity": 0.45 + (thin_score * 0.28),
        "sound": 0.45 + (thin_score * 0.20),
        "string_movement": 0.50 + (thin_score * 0.12),
        "tension_retention": 0.45 + (thick_score * 0.24),
        "value_for_money": 0.50,
    }
    scores["stability_score"] = (
        (scores["durability"] * 0.45)
        + (scores["tension_retention"] * 0.35)
        + (scores["control"] * 0.20)
    )
    scores["all_round_score"] = (
        scores["attack"]
        + scores["comfort"]
        + scores["control"]
        + scores["durability"]
        + scores["elasticity"]
        + scores["tension_retention"]
    ) / 6
    scores["attacking_fit_score"] = (
        (scores["attack"] * 0.55)
        + (scores["elasticity"] * 0.30)
        + (scores["sound"] * 0.15)
    )
    scores["control_fit_score"] = (
        (scores["control"] * 0.55)
        + (scores["comfort"] * 0.20)
        + (scores["durability"] * 0.25)
    )
    scores["beginner_fit_score"] = (
        (scores["comfort"] * 0.35)
        + (scores["control"] * 0.25)
        + (scores["durability"] * 0.25)
        + (scores["value_for_money"] * 0.15)
    )
    return {key: clamp01(value) for key, value in scores.items()}


def _community_feature_scores(item: StringItem) -> dict[str, float]:
    if not item.tags and item.community_rating is None:
        return {}
    scores = {feature_key: 0.5 for feature_key in ALL_FEATURES}
    for tag in item.tags:
        effect = COMMUNITY_TAG_EFFECTS.get(tag.tag_label)
        if effect is None:
            effect = COMMUNITY_TAG_EFFECTS.get(tag.tag_key)
        if effect is None:
            continue
        weight = min(1.0, max(tag.tag_count, 1) / 10)
        for feature_key, delta in effect.items():
            scores[feature_key] = clamp01(scores[feature_key] + (delta * weight))

    if item.community_rating is not None:
        rating_delta = ((item.community_rating - 7.0) / 3.0) * 0.08
        scores["all_round_score"] = clamp01(scores["all_round_score"] + rating_delta)
        scores["value_for_money"] = clamp01(
            scores["value_for_money"] + (rating_delta * 0.8)
        )
    if item.review_count >= 100:
        scores["stability_score"] = clamp01(scores["stability_score"] + 0.05)
    return scores


def _preference_match_score(
    *,
    fused_scores: dict[str, float],
    item: StringItem,
    preference_rows: list[dict[str, float | str | None]],
) -> float:
    weighted_total = 0.0
    total_weight = 0.0
    for row in preference_rows:
        feature_key = _domain_feature_key(str(row["feature_key"]))
        weight = float(row.get("preference_weight") or 0)
        if feature_key in PRIMARY_FEATURES:
            weighted_total += fused_scores.get(feature_key, 0.5) * weight
            total_weight += weight
        elif feature_key == "gauge_mm" and item.gauge_main_mm is not None:
            weighted_total += (
                _range_fit(
                    item.gauge_main_mm,
                    row.get("preferred_min"),
                    row.get("preferred_max"),
                    tolerance=0.03,
                )
                * weight
            )
            total_weight += weight
    if total_weight == 0:
        return 0.5
    return clamp01(weighted_total / total_weight)


def _nlp_review_score(
    *,
    matrix_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
) -> float:
    if not matrix_scores:
        return 0.5
    weighted_total = 0.0
    total_weight = 0.0
    for row in preference_rows:
        feature_key = _domain_feature_key(str(row["feature_key"]))
        weight = float(row.get("preference_weight") or 0)
        if feature_key not in PRIMARY_FEATURES:
            continue
        value = matrix_scores.get(feature_key)
        if value is None:
            continue
        weighted_total += value * weight
        total_weight += weight
    if total_weight == 0:
        return 0.5
    return clamp01(weighted_total / total_weight)


def _budget_fit_score(
    price_rm: float | None,
    request: RecommendationRequestModel,
) -> float:
    if price_rm is None:
        return 0.5
    budget_min = request.budget_min
    budget_max = request.budget_max
    if budget_min <= price_rm <= budget_max:
        span = max(budget_max - budget_min, 10)
        midpoint = (budget_min + budget_max) / 2
        closeness = 1 - min(abs(price_rm - midpoint) / span, 1)
        return clamp01(max(0.8, closeness))

    gap = budget_min - price_rm if price_rm < budget_min else price_rm - budget_max
    tolerance = max((budget_max - budget_min) or budget_max or budget_min or 10, 10)
    return clamp01(0.8 - (gap / tolerance))


def _rule_fit_score(
    *,
    item: StringItem,
    fused_scores: dict[str, float],
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

    if request.skill_level == "beginner" and (item.gauge_main_mm or 0.66) <= 0.63:
        apply(
            -0.18,
            "penalizes an ultra-thin gauge for beginner play",
            "beginner_thin_gauge_penalty",
        )
    if request.skill_level == "beginner" and fused_scores["beginner_fit_score"] >= 0.68:
        apply(
            0.10,
            "safer feel and stability for a beginner profile",
            "beginner_fit_bonus",
        )

    if request.playing_style == "attacking" and fused_scores["attack"] >= 0.72:
        apply(0.12, "fits your attacking playing style", "attacking_repulsion_bonus")
    if request.playing_style == "control_defensive" and fused_scores["control"] >= 0.72:
        apply(0.12, "fits your control-oriented playing style", "control_bonus")
    if request.playing_style == "balanced" and fused_scores["all_round_score"] >= 0.68:
        apply(0.08, "offers a balanced all-round response", "balanced_bonus")

    if (
        request.frequency_per_week >= 3
        and ((fused_scores["stability_score"] + fused_scores["tension_retention"]) / 2)
        >= 0.68
    ):
        apply(
            0.08,
            "supports frequent play with better stability and tension retention",
            "frequent_play_bonus",
        )

    if request.budget_max <= 40 and fused_scores["value_for_money"] <= 0.45:
        apply(
            -0.08,
            "penalizes weak value-for-money for a tighter budget",
            "low_budget_value_penalty",
        )
    if request.budget_max <= 40 and fused_scores["value_for_money"] >= 0.70:
        apply(
            0.06,
            "rewards better value-for-money for a tighter budget",
            "low_budget_value_bonus",
        )

    if request.preferred_tension >= 27 and (item.gauge_main_mm or 0.66) >= 0.67:
        apply(
            0.06,
            "aligns with your higher preferred tension",
            "high_tension_gauge_bonus",
        )
    if request.preferred_tension <= 23 and fused_scores["comfort"] >= 0.65:
        apply(
            0.05,
            "aligns with your lower-tension comfort preference",
            "low_tension_comfort_bonus",
        )

    return score, reasons, events


def _build_reasons(
    *,
    item: StringItem,
    request: RecommendationRequestModel,
    fused_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
    budget_fit: float,
    rule_reasons: list[str],
) -> list[str]:
    reasons: list[str] = []
    for feature_key, label in _top_weighted_preference_reasons(
        fused_scores,
        preference_rows,
    ):
        reasons.append(f"matches your {label} preference")
    if budget_fit >= 0.8 and item.price_rm is not None:
        reasons.append("within your budget range")
    elif budget_fit >= 0.55 and item.price_rm is not None:
        reasons.append("close to your budget range")
    reasons.extend(rule_reasons)
    if request.playing_style == "attacking" and fused_scores["attack"] >= 0.75:
        reasons.append("strong repulsion and response for attacking rallies")
    if request.playing_style == "control_defensive" and fused_scores["control"] >= 0.75:
        reasons.append("control-oriented response for placement and touch")
    return _unique(reasons)[:4]


def _top_weighted_preference_reasons(
    fused_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
) -> list[tuple[str, str]]:
    labels = {
        "attack": "attack",
        "comfort": "comfort",
        "control": "control",
        "durability": "durability",
        "elasticity": "repulsion",
        "sound": "hitting sound",
        "string_movement": "string-bed feel",
        "tension_retention": "tension retention",
        "value_for_money": "value-for-money",
    }
    ranked = []
    for row in preference_rows:
        feature_key = _domain_feature_key(str(row["feature_key"]))
        if feature_key not in PRIMARY_FEATURES:
            continue
        weight = float(row.get("preference_weight") or 0)
        ranked.append((weight * fused_scores.get(feature_key, 0.5), feature_key))
    ranked.sort(reverse=True)
    return [(feature_key, labels[feature_key]) for _, feature_key in ranked[:2]]


def _preferred_gauge_range(
    request: RecommendationRequestModel,
) -> tuple[float, float]:
    center = 0.66
    if request.preferred_tension >= 28:
        center += 0.03
    elif request.preferred_tension >= 26:
        center += 0.01
    elif request.preferred_tension <= 23:
        center -= 0.02

    if request.skill_level == "beginner":
        center += 0.01
    elif request.skill_level == "advanced" and request.playing_style == "attacking":
        center -= 0.01

    center = min(max(center, 0.61), 0.70)
    return round(center - 0.02, 2), round(center + 0.02, 2)


def _range_fit(
    value: float,
    preferred_min: float | str | None,
    preferred_max: float | str | None,
    *,
    tolerance: float,
) -> float:
    if preferred_min is None or preferred_max is None:
        return 0.5
    low = float(preferred_min)
    high = float(preferred_max)
    if low <= value <= high:
        return 1.0
    if value < low:
        return clamp01(1 - ((low - value) / tolerance))
    return clamp01(1 - ((value - high) / tolerance))


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _storage_feature_key(feature_key: str) -> str:
    return DOMAIN_TO_STORAGE_FEATURE_KEY.get(feature_key, feature_key)


def _domain_feature_key(feature_key: str) -> str:
    return STORAGE_TO_DOMAIN_FEATURE_KEY.get(feature_key, feature_key)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
