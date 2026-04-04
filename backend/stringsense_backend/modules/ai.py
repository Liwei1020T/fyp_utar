from __future__ import annotations

from collections import defaultdict
from math import inf
from typing import Iterable

from ai_service.data_loader import load_review_signals
from ai_service.schemas import RagQueryRequest
from ai_service.schemas import RagQueryResponse
from ai_service.schemas import RecommendationRequest
from ai_service.schemas import RecommendationResponse
from ai_service.schemas import RecommendationResult
from ai_service.schemas import ReviewAnalyzeRequest
from ai_service.schemas import ReviewAnalyzeResponse
from ai_service.schemas import ReviewAspectSignal
from ai_service.schemas import StringRecord

from stringsense_backend.core.serialization import decimal_to_float
from stringsense_backend.db.models import StringCatalogItem

ALGORITHM_VERSION = "unified_python_rule_engine_v1"

REVIEW_KEYWORDS: dict[str, tuple[str, ...]] = {
    "attack": ("power", "smash", "repulsion", "弹性"),
    "comfort": ("comfort", "soft", "arm", "手感"),
    "control": ("control", "placement", "控球"),
    "durability": ("durable", "durability", "耐打"),
    "sound": ("sound", "crisp", "声音"),
    "tension_retention": ("tension", "drop", "掉磅"),
}


class UnifiedAIService:
    def recommend(
        self,
        catalog: Iterable[StringCatalogItem],
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        scored_items = []
        for item in catalog:
            record = self._to_record(item)
            score, reasons = self._score_item(record, request)
            scored_items.append((record, round(score, 4), reasons))

        scored_items.sort(
            key=lambda row: (
                -row[1],
                row[0].price_rm if row[0].price_rm is not None else inf,
                row[0].brand,
                row[0].model_name,
            )
        )

        results = [
            RecommendationResult(
                rank=index,
                string_name=f"{item.brand} {item.model_name}",
                brand=item.brand,
                score=score,
                price_rm=item.price_rm,
                aspect_scores=self._aspect_scores(item),
                reasons=reasons[:3],
            )
            for index, (item, score, reasons) in enumerate(
                scored_items[: request.top_n],
                start=1,
            )
        ]
        return RecommendationResponse(
            algorithm_version=ALGORITHM_VERSION,
            results=results,
        )

    def analyze_reviews(self, request: ReviewAnalyzeRequest) -> ReviewAnalyzeResponse:
        aggregated: dict[str, list[str]] = defaultdict(list)
        for review in request.reviews:
            lowered = review.lower()
            for aspect, keywords in REVIEW_KEYWORDS.items():
                if any(keyword.lower() in lowered for keyword in keywords):
                    aggregated[aspect].append(review)

        if not aggregated:
            for row in load_review_signals()[:3]:
                aspect = row.get("aspect") or row.get("aspect_name") or "general"
                aggregated[aspect].append(
                    "Loaded from review-aspect signals reference."
                )

        aspects = [
            ReviewAspectSignal(
                aspect=aspect,
                score=round(min(1.0, 0.35 + (len(evidence) * 0.15)), 2),
                evidence=evidence[:3],
            )
            for aspect, evidence in aggregated.items()
        ]
        aspects.sort(key=lambda item: (-item.score, item.aspect))
        return ReviewAnalyzeResponse(review_count=len(request.reviews), aspects=aspects)

    def rag_query(
        self,
        catalog: Iterable[StringCatalogItem],
        request: RagQueryRequest,
    ) -> RagQueryResponse:
        query_terms = set(request.query.lower().split())
        matches = []
        for item in catalog:
            record = self._to_record(item)
            haystack = {
                term
                for term in (
                    f"{record.brand} {record.model_name} {record.normalized_name}"
                )
                .lower()
                .split()
            }
            overlap = sorted(query_terms & haystack)
            if overlap:
                matches.append(
                    {
                        "string_name": f"{record.brand} {record.model_name}",
                        "brand": record.brand,
                        "matched_terms": overlap,
                    }
                )
        return RagQueryResponse(
            query=request.query,
            top_k=request.top_k,
            matches=matches[: request.top_k],
        )

    def _to_record(self, item: StringCatalogItem) -> StringRecord:
        return StringRecord(
            brand=item.brand,
            model_name=item.model_name,
            normalized_name=item.normalized_name,
            price_rm=decimal_to_float(item.price_rm),
            attack=float(item.attack),
            comfort=float(item.comfort),
            control=float(item.control),
            durability=float(item.durability),
            elasticity=float(item.elasticity),
            sound=float(item.sound),
            string_movement=float(item.string_movement),
            tension_retention=float(item.tension_retention),
            value_for_money=float(item.value_for_money),
            beginner_fit_score=float(item.beginner_fit_score),
            stability_score=float(item.stability_score),
            all_round_score=float(item.all_round_score),
            source_item_id=item.source_item_id,
            source_url=item.source_url,
        )

    def _score_item(
        self,
        item: StringRecord,
        request: RecommendationRequest,
    ) -> tuple[float, list[str]]:
        aspect_scores = self._aspect_scores(item)
        weights = {
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
        weighted_total = sum(weights[key] * aspect_scores[key] for key in weights)
        content_score = weighted_total / max(sum(weights.values()), 1e-6)

        rule_adjustment = 0.0
        reasons: list[str] = []

        if request.playing_style == "attacking":
            rule_adjustment += (
                (item.attack * 0.10) + (item.elasticity * 0.08) + (item.sound * 0.05)
            )
            reasons.append("Matches your attacking playing style")
        elif request.playing_style == "control_defensive":
            rule_adjustment += (
                (item.control * 0.10) + (item.comfort * 0.08) + (item.durability * 0.05)
            )
            reasons.append("Supports your control and defensive priorities")
        else:
            rule_adjustment += item.all_round_score * 0.08
            reasons.append("Offers a balanced all-round profile")

        if request.skill_level == "beginner":
            rule_adjustment += (
                item.beginner_fit_score * 0.12
                + item.comfort * 0.05
                + item.value_for_money * 0.05
            )
            reasons.append("Beginner-friendly comfort and value fit")
        elif request.skill_level == "advanced":
            rule_adjustment += (item.attack * 0.04) + (item.control * 0.04)
            reasons.append("Responsive enough for advanced play")

        if request.frequency_per_week >= 3:
            rule_adjustment += (item.stability_score * 0.08) + (
                item.tension_retention * 0.06
            )
            reasons.append("Stability and tension retention help frequent play")

        if request.game_type == "doubles":
            rule_adjustment += (item.attack * 0.04) + (item.sound * 0.03)
            reasons.append("Suited to faster doubles exchanges")
        else:
            rule_adjustment += (item.control * 0.03) + (item.comfort * 0.02)
            reasons.append("Control and touch help singles rallies")

        if item.price_rm is not None:
            if item.price_rm < request.budget_min:
                rule_adjustment -= min(0.15, (request.budget_min - item.price_rm) / 100)
                reasons.append("Below your target budget range")
            elif item.price_rm > request.budget_max:
                rule_adjustment -= min(0.20, (item.price_rm - request.budget_max) / 100)
                reasons.append("Above your budget range")
            else:
                rule_adjustment += 0.06
                reasons.append("Falls within your budget range")

        if request.preferred_tension >= 27 and item.stability_score >= 0.6:
            rule_adjustment += 0.04
            reasons.append("Stability profile suits higher tensions")
        elif request.preferred_tension <= 23 and item.comfort >= 0.6:
            rule_adjustment += 0.03
            reasons.append("Comfort profile suits lower tension preferences")

        top_aspects = sorted(
            aspect_scores.items(),
            key=lambda pair: pair[1],
            reverse=True,
        )[:2]
        if top_aspects:
            reasons.append(
                "Strong "
                + " and ".join(aspect.replace("_", " ") for aspect, _ in top_aspects)
                + " scores"
            )

        final_score = max(0.0, min(1.0, (content_score * 0.75) + rule_adjustment))
        return final_score, unique(reasons)

    @staticmethod
    def _aspect_scores(item: StringRecord) -> dict[str, float]:
        return {
            "attack": item.attack,
            "comfort": item.comfort,
            "control": item.control,
            "durability": item.durability,
            "elasticity": item.elasticity,
            "sound": item.sound,
            "string_movement": item.string_movement,
            "tension_retention": item.tension_retention,
            "value_for_money": item.value_for_money,
        }


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


ai_service = UnifiedAIService()
