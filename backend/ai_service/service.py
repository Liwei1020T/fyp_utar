from __future__ import annotations

from collections import defaultdict

from ai_service.data_loader import extract_ascii_words
from ai_service.data_loader import load_review_signals
from ai_service.data_loader import load_string_matrix
from ai_service.data_loader import normalize_catalog_name
from ai_service.data_loader import normalize_lookup_name
from ai_service.schemas import ExplainRequest
from ai_service.schemas import ExplainResponse
from ai_service.schemas import RagQueryRequest
from ai_service.schemas import RagQueryResponse
from ai_service.schemas import RecommendationRequest
from ai_service.schemas import RecommendationResponse
from ai_service.schemas import RecommendationResult
from ai_service.schemas import ReviewAnalyzeRequest
from ai_service.schemas import ReviewAnalyzeResponse
from ai_service.schemas import ReviewAspectSignal
from ai_service.schemas import StringRecord


ALGORITHM_VERSION = "practical_matrix_v8_rule_content_v2"

REVIEW_KEYWORDS: dict[str, tuple[str, ...]] = {
    "attack": ("power", "smash", "repulsion", "弹性"),
    "comfort": ("comfort", "soft", "arm", "手感"),
    "control": ("control", "placement", "控球"),
    "durability": ("durable", "durability", "耐打"),
    "sound": ("sound", "crisp", "声音"),
    "tension_retention": ("tension", "drop", "掉磅"),
}


class RecommendationService:
    def __init__(self) -> None:
        self._matrix = load_string_matrix()
        self._lookup_index = _build_string_lookup_index(self._matrix)

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "service": "ai",
            "matrix_loaded": len(self._matrix),
            "algorithm_version": ALGORITHM_VERSION,
        }

    def list_strings(self) -> list[dict[str, object]]:
        return [
            {
                "brand": item.brand,
                "model_name": item.model_name,
                "normalized_name": item.normalized_name,
                "price_rm": item.price_rm,
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
            for item in self._matrix
        ]

    def get_string(self, string_name: str) -> dict[str, object]:
        for target in _lookup_targets(string_name):
            item = self._lookup_index.get(target)
            if item is not None:
                return item.model_dump()
        raise KeyError(string_name)

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        scored_items = []
        for item in self._matrix:
            score, reasons = self._score_item(item, request)
            scored_items.append((item, round(score, 4), reasons))

        scored_items.sort(
            key=lambda row: (
                -row[1],
                row[0].price_rm if row[0].price_rm is not None else 10_000,
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

    def explain(self, request: ExplainRequest) -> ExplainResponse:
        item = StringRecord.model_validate(self.get_string(request.string_name))
        _, reasons = self._score_item(item, request.user_context)
        return ExplainResponse(
            algorithm_version=ALGORITHM_VERSION,
            string_name=f"{item.brand} {item.model_name}",
            reasons=reasons[:5],
            aspect_scores=self._aspect_scores(item),
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

    def rag_query(self, request: RagQueryRequest) -> RagQueryResponse:
        query_terms = set(request.query.lower().split())
        matches = []
        for item in self._matrix:
            haystack = {
                term
                for term in f"{item.brand} {item.model_name} {item.normalized_name}".lower().split()
            }
            overlap = sorted(query_terms & haystack)
            if overlap:
                matches.append(
                    {
                        "string_name": f"{item.brand} {item.model_name}",
                        "brand": item.brand,
                        "matched_terms": overlap,
                    }
                )

        return RagQueryResponse(
            query=request.query,
            top_k=request.top_k,
            matches=matches[: request.top_k],
        )

    def _score_item(
        self,
        item: StringRecord,
        request: RecommendationRequest,
    ) -> tuple[float, list[str]]:
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
        weighted_total = sum(
            weights[key] * self._aspect_scores(item)[key] for key in weights
        )
        content_score = weighted_total / max(sum(weights.values()), 1e-6)

        rule_adjustment = 0.0
        reasons: list[str] = []

        if request.playing_style == "attacking":
            bonus = (item.attack * 0.1) + (item.elasticity * 0.08) + (item.sound * 0.05)
            rule_adjustment += bonus
            reasons.append("Matches your attacking playing style")
        elif request.playing_style == "control_defensive":
            bonus = (
                (item.control * 0.1) + (item.comfort * 0.08) + (item.durability * 0.05)
            )
            rule_adjustment += bonus
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
            frequent_bonus = (item.stability_score * 0.08) + (
                item.tension_retention * 0.06
            )
            rule_adjustment += frequent_bonus
            reasons.append("Stability and tension retention help frequent play")

        if request.preferred_tension >= 27 and item.stability_score >= 0.6:
            rule_adjustment += 0.04
            reasons.append("Stability profile suits higher tensions")
        elif request.preferred_tension <= 23 and item.comfort >= 0.6:
            rule_adjustment += 0.03
            reasons.append("Comfort profile suits lower tension preferences")

        top_aspects = sorted(
            self._aspect_scores(item).items(),
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
        return final_score, _unique(reasons)

    def _aspect_scores(self, item: StringRecord) -> dict[str, float]:
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


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _string_lookup_aliases(item: StringRecord) -> set[str]:
    aliases = {
        item.normalized_name.strip(),
        normalize_catalog_name(item.brand, item.model_name),
        normalize_catalog_name("", item.model_name).strip(),
        normalize_lookup_name(item.normalized_name),
        normalize_lookup_name(f"{item.brand} {item.model_name}"),
        normalize_lookup_name(item.model_name),
    }

    ascii_brand = extract_ascii_words(item.brand)
    if ascii_brand:
        aliases.add(normalize_catalog_name(ascii_brand, item.model_name))
        aliases.add(normalize_lookup_name(f"{ascii_brand} {item.model_name}"))

    return {alias for alias in aliases if alias}


def _lookup_targets(value: str) -> set[str]:
    return {
        normalize_catalog_name("", value).strip(),
        normalize_lookup_name(value),
    }


def _build_string_lookup_index(
    items: list[StringRecord],
) -> dict[str, StringRecord]:
    lookup_index: dict[str, StringRecord] = {}

    for item in items:
        for alias in _string_lookup_aliases(item):
            lookup_index.setdefault(alias, item)

    return lookup_index
