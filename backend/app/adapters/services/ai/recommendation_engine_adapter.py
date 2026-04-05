from __future__ import annotations

from typing import Sequence

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
from app.domain.recommendation.entities import RecommendationResultModel


ALGORITHM_VERSION = "unified_python_rule_engine_v1"


class RecommendationEngineAdapter:
    def recommend(
        self,
        catalog: Sequence[StringItem],
        request: RecommendationRequestModel,
    ) -> RecommendationResponseModel:
        scored_items: list[tuple[StringItem, float, list[str]]] = []
        for item in catalog:
            score, reasons = self._score_item(item, request)
            scored_items.append((item, round(score, 4), reasons))

        scored_items.sort(
            key=lambda row: (
                -row[1],
                row[0].price_rm if row[0].price_rm is not None else float("inf"),
                row[0].brand,
                row[0].model_name,
            )
        )
        results = [
            RecommendationResultModel(
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
        return RecommendationResponseModel(
            algorithm_version=ALGORITHM_VERSION,
            results=results,
        )

    def _aspect_scores(self, item: StringItem) -> dict[str, float]:
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

    def _score_item(
        self,
        item: StringItem,
        request: RecommendationRequestModel,
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
                reasons.append("Above your target budget range")
            else:
                reasons.append("Fits within your budget range")

        final_score = max(0.0, min(1.0, (content_score * 0.78) + rule_adjustment))
        return final_score, reasons

