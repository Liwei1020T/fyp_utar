from __future__ import annotations

from dataclasses import dataclass

from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
from app.ports.repositories.catalog_repository import CatalogRepository
from app.ports.repositories.profile_repository import ProfileRepository
from app.ports.repositories.recommendation_log_repository import (
    RecommendationLogRepository,
)
from app.ports.services.recommendation_engine import RecommendationEngine
from app.shared.errors import BadRequestError
from app.shared.errors import NotFoundError


@dataclass
class GenerateRecommendationUseCase:
    catalog_repository: CatalogRepository
    profile_repository: ProfileRepository
    recommendation_engine: RecommendationEngine
    recommendation_log_repository: RecommendationLogRepository

    def execute_preview(
        self,
        *,
        user_id: str | None,
        request: RecommendationRequestModel,
    ) -> RecommendationResponseModel:
        catalog = self.catalog_repository.list_active_catalog()
        result = self.recommendation_engine.recommend(catalog, request)
        self.recommendation_log_repository.create_log(
            user_id=user_id,
            request_payload=request.__dict__,
            response_payload={
                "algorithm_version": result.algorithm_version,
                "results": [item.__dict__ for item in result.results],
            },
            algorithm_version=result.algorithm_version,
        )
        return result

    def execute_profile(
        self,
        *,
        user_id: str,
        top_n: int,
    ) -> RecommendationResponseModel:
        profile = self.profile_repository.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Profile not found")
        missing_fields = [
            field
            for field, value in profile.__dict__.items()
            if field
            in {
                "skill_level",
                "playing_style",
                "budget_min",
                "budget_max",
                "preferred_tension",
                "game_type",
                "frequency_per_week",
                "pref_attack",
                "pref_comfort",
                "pref_control",
                "pref_durability",
                "pref_elasticity",
                "pref_sound",
                "pref_string_movement",
                "pref_tension_retention",
                "pref_value_for_money",
            }
            and value is None
        ]
        if missing_fields:
            raise BadRequestError("Profile is incomplete for recommendation")
        request = RecommendationRequestModel(
            user_id=user_id,
            skill_level=profile.skill_level or "",
            playing_style=profile.playing_style or "",
            budget_min=profile.budget_min or 0,
            budget_max=profile.budget_max or 0,
            preferred_tension=profile.preferred_tension or 0,
            game_type=profile.game_type or "",
            frequency_per_week=profile.frequency_per_week or 0,
            pref_attack=profile.pref_attack or 0,
            pref_comfort=profile.pref_comfort or 0,
            pref_control=profile.pref_control or 0,
            pref_durability=profile.pref_durability or 0,
            pref_elasticity=profile.pref_elasticity or 0,
            pref_sound=profile.pref_sound or 0,
            pref_string_movement=profile.pref_string_movement or 0,
            pref_tension_retention=profile.pref_tension_retention or 0,
            pref_value_for_money=profile.pref_value_for_money or 0,
            top_n=top_n,
        )
        return self.execute_preview(user_id=user_id, request=request)

