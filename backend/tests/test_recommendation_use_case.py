from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.shared.pagination import Page
from app.use_cases.recommendation.generate_recommendation import (
    GenerateRecommendationUseCase,
)


class FakeCatalogRepository:
    def get_by_id(self, string_id: str, *, include_inactive: bool = False):
        raise NotImplementedError

    def list_strings(self, **kwargs):
        raise NotImplementedError

    def list_inventory(self, **kwargs):
        raise NotImplementedError

    def create(self, values: dict[str, object]):
        raise NotImplementedError

    def update(self, string_id: str, values: dict[str, object]):
        raise NotImplementedError

    def deactivate(self, string_id: str):
        raise NotImplementedError

    def update_inventory(self, string_id: str, values: dict[str, object]):
        raise NotImplementedError

    def list_active_catalog(self) -> list[StringItem]:
        return [
            StringItem(
                id="string-1",
                brand="Yonex",
                model_name="BG80",
                normalized_name="yonex bg80",
                price_rm=45.0,
                attack=0.9,
                comfort=0.5,
                control=0.7,
                durability=0.6,
                elasticity=0.8,
                sound=0.7,
                string_movement=0.4,
                tension_retention=0.6,
                value_for_money=0.5,
                beginner_fit_score=0.4,
                stability_score=0.6,
                all_round_score=0.7,
                source_item_id=None,
                source_url=None,
                stock_level=10,
                admin_note=None,
                is_active=True,
                created_at=None,
                updated_at=None,
            )
        ]


class FakeProfileRepository:
    def get_by_user_id(self, user_id: str):  # pragma: no cover - not used here
        raise AssertionError("profile lookup should not be used for preview requests")

    def upsert(self, profile):  # pragma: no cover - not used here
        raise NotImplementedError


@dataclass
class FakeRecommendationEngine:
    seen_catalog_size: int = 0

    def recommend(
        self,
        catalog: Sequence[StringItem],
        request: RecommendationRequestModel,
    ) -> RecommendationResponseModel:
        self.seen_catalog_size = len(catalog)
        return RecommendationResponseModel(
            algorithm_version="test-engine-v1",
            results=[
                RecommendationResultModel(
                    rank=1,
                    string_name="Yonex BG80",
                    brand="Yonex",
                    score=0.91,
                    price_rm=45.0,
                    aspect_scores={"attack": 0.9},
                    reasons=["Matches your attacking playing style"],
                )
            ],
        )


@dataclass
class FakeRecommendationLogRepository:
    last_log: dict[str, object] | None = None

    def create_log(
        self,
        *,
        user_id: str | None,
        request_payload: dict[str, object],
        response_payload: dict[str, object],
        algorithm_version: str,
    ) -> None:
        self.last_log = {
            "user_id": user_id,
            "request_payload": request_payload,
            "response_payload": response_payload,
            "algorithm_version": algorithm_version,
        }

    def list_logs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page:
        raise NotImplementedError


def test_generate_recommendation_use_case_logs_preview_requests() -> None:
    engine = FakeRecommendationEngine()
    logs = FakeRecommendationLogRepository()
    use_case = GenerateRecommendationUseCase(
        catalog_repository=FakeCatalogRepository(),
        profile_repository=FakeProfileRepository(),
        recommendation_engine=engine,
        recommendation_log_repository=logs,
    )

    result = use_case.execute_preview(
        user_id="user-1",
        request=RecommendationRequestModel(
            user_id="user-1",
            skill_level="advanced",
            playing_style="attacking",
            budget_min=40,
            budget_max=70,
            preferred_tension=25,
            game_type="doubles",
            frequency_per_week=3,
            pref_attack=5,
            pref_comfort=3,
            pref_control=4,
            pref_durability=3,
            pref_elasticity=5,
            pref_sound=4,
            pref_string_movement=3,
            pref_tension_retention=4,
            pref_value_for_money=3,
            top_n=3,
        ),
    )

    assert engine.seen_catalog_size == 1
    assert result.algorithm_version == "test-engine-v1"
    assert logs.last_log is not None
    assert logs.last_log["user_id"] == "user-1"
    assert logs.last_log["algorithm_version"] == "test-engine-v1"
