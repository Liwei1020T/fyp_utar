from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from app.domain.profile.entities import PlayerProfile
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.scoring import Fyp1ContentRecommendationScorer
from app.domain.recommendation.scoring import PREFERENCE_SOURCE_LAYER
from app.ports.repositories.profile_repository import ProfileRepository
from app.ports.repositories.recommendation_repository import RecommendationRepository


@dataclass
class UpsertMyProfileUseCase:
    profile_repository: ProfileRepository
    recommendation_repository: RecommendationRepository
    scorer: Fyp1ContentRecommendationScorer = field(
        default_factory=Fyp1ContentRecommendationScorer
    )

    def execute(
        self,
        profile: PlayerProfile,
        *,
        username: str | None = None,
    ) -> PlayerProfile:
        saved = self.profile_repository.upsert(
            profile,
            username=username,
        )
        if _is_complete(saved):
            request = RecommendationRequestModel(
                user_id=saved.user_id,
                skill_level=saved.skill_level or "",
                playing_style=saved.playing_style or "",
                budget_tier=saved.budget_tier or "between_30_50",
                preferred_tension=saved.preferred_tension or 0,
                game_type=saved.game_type or "",
                frequency_per_week=saved.frequency_per_week or 0,
                pref_attack=saved.pref_attack or 0,
                pref_comfort=saved.pref_comfort or 0,
                pref_control=saved.pref_control or 0,
                pref_durability=saved.pref_durability or 0,
                pref_elasticity=saved.pref_elasticity or 0,
                pref_sound=saved.pref_sound or 0,
                pref_string_movement=saved.pref_string_movement or 0,
                pref_tension_retention=saved.pref_tension_retention or 0,
                pref_value_for_money=saved.pref_value_for_money or 0,
                top_n=5,
            )
            self.recommendation_repository.replace_user_preference_vector(
                user_id=saved.user_id,
                source_layer=PREFERENCE_SOURCE_LAYER,
                entries=self.scorer.build_preference_vector(
                    user_id=saved.user_id,
                    request=request,
                ),
            )
        return saved


def _is_complete(profile: PlayerProfile) -> bool:
    return all(
        value is not None
        for value in (
            profile.skill_level,
            profile.playing_style,
            profile.budget_tier,
            profile.preferred_tension,
            profile.game_type,
            profile.frequency_per_week,
            profile.pref_attack,
            profile.pref_comfort,
            profile.pref_control,
            profile.pref_durability,
            profile.pref_elasticity,
            profile.pref_sound,
            profile.pref_string_movement,
            profile.pref_tension_retention,
            profile.pref_value_for_money,
        )
    )
