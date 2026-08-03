from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import StringInventoryItem
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.models import UserPreferenceMatrix
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_string_item
from app.domain.catalog.recommendation_features import domain_feature_key
from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import RecommendationFeatureSignalModel
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import UserPreferenceVectorEntry
from app.shared.serialization import number_to_float


class SqlAlchemyRecommendationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active_candidates(self) -> list[RecommendationCandidateModel]:
        items = (
            self.db.execute(
                select(StringCatalogItem)
                .options(
                    selectinload(StringCatalogItem.brand_ref),
                    selectinload(StringCatalogItem.metrics),
                    selectinload(StringCatalogItem.tags),
                    selectinload(StringCatalogItem.official_performance),
                    selectinload(StringCatalogItem.inventory_item).selectinload(
                        StringInventoryItem.movements
                    ),
                    selectinload(StringCatalogItem.recommendation_entries),
                )
                .where(StringCatalogItem.is_active.is_(True))
                .order_by(
                    StringCatalogItem.brand_code.asc(),
                    StringCatalogItem.display_name.asc(),
                )
            )
            .unique()
            .scalars()
            .all()
        )
        return [
            RecommendationCandidateModel(
                item=to_string_item(item),
                matrix_by_source=_matrix_by_source(item.recommendation_entries),
            )
            for item in items
        ]

    def replace_user_preference_vector(
        self,
        *,
        user_id: str,
        source_layer: str,
        entries: list[dict[str, float | str | None]],
    ) -> list[UserPreferenceVectorEntry]:
        self._lock_user(user_id)
        self.db.execute(
            delete(UserPreferenceMatrix).where(
                UserPreferenceMatrix.user_id == user_id,
                UserPreferenceMatrix.source_layer == source_layer,
            )
        )
        for entry in entries:
            self.db.add(
                UserPreferenceMatrix(
                    user_id=user_id,
                    feature_key=str(entry["feature_key"]),
                    source_layer=source_layer,
                    raw_score=entry.get("raw_score"),
                    preference_weight=entry.get("preference_weight"),
                    preferred_min=entry.get("preferred_min"),
                    preferred_max=entry.get("preferred_max"),
                )
            )
        self.db.flush()
        return self.list_user_preference_vector(
            user_id=user_id,
            source_layer=source_layer,
        )

    def list_user_preference_vector(
        self,
        *,
        user_id: str,
        source_layer: str | None = None,
    ) -> list[UserPreferenceVectorEntry]:
        query = (
            select(UserPreferenceMatrix)
            .where(UserPreferenceMatrix.user_id == user_id)
            .order_by(
                UserPreferenceMatrix.source_layer.asc(),
                UserPreferenceMatrix.feature_key.asc(),
            )
        )
        if source_layer is not None:
            query = query.where(UserPreferenceMatrix.source_layer == source_layer)
        items = self.db.execute(query).scalars().all()
        return [_to_preference_entry(item) for item in items]

    def replace_score_cache(
        self,
        *,
        user_id: str,
        algorithm_version: str,
        results: list[dict[str, object]],
    ) -> list[CachedRecommendationRecord]:
        self._lock_user(user_id)
        self.db.execute(
            delete(RecommendationScoreCache).where(
                RecommendationScoreCache.user_id == user_id,
                RecommendationScoreCache.algorithm_version == algorithm_version,
            )
        )
        for result in results:
            preference_match = _float_or_none(result.get("preference_match_score"))
            rule_fit = _float_or_none(result.get("rule_fit_score"))
            budget_fit = _float_or_none(result.get("budget_fit_score"))
            confidence_score = _float_or_none(result.get("confidence_score"))
            nlp_review_score = _float_or_none(result.get("nlp_review_score"))
            rationale = _required_mapping(result, "rationale")
            self.db.add(
                RecommendationScoreCache(
                    user_id=user_id,
                    catalog_id=str(result["catalog_id"]),
                    algorithm_version=algorithm_version,
                    content_score=preference_match,
                    collaborative_score=None,
                    rule_score=rule_fit,
                    nlp_score=nlp_review_score,
                    preference_match_score=preference_match,
                    rule_fit_score=rule_fit,
                    budget_fit_score=budget_fit,
                    confidence_score=confidence_score,
                    nlp_review_score=nlp_review_score,
                    final_score=_required_float(result, "final_score"),
                    rank_position=_required_int(result, "rank_position"),
                    rationale=rationale,
                    matrix_version=_optional_string(
                        result.get("matrix_version") or rationale.get("matrix_version")
                    ),
                    feature_source_version=_optional_string(
                        result.get("feature_source_version")
                        or rationale.get("feature_source_version")
                    ),
                )
            )
        self.db.flush()
        return self.get_cached_results(
            user_id=user_id,
            algorithm_version=algorithm_version,
        )

    def get_cached_results(
        self,
        *,
        user_id: str,
        algorithm_version: str | None = None,
    ) -> list[CachedRecommendationRecord]:
        if algorithm_version is None:
            latest = (
                self.db.execute(
                    select(RecommendationScoreCache)
                    .where(RecommendationScoreCache.user_id == user_id)
                    .order_by(
                        RecommendationScoreCache.generated_at.desc(),
                        RecommendationScoreCache.algorithm_version.desc(),
                    )
                )
                .scalars()
                .first()
            )
            if latest is None:
                return []
            algorithm_version = latest.algorithm_version

        items = (
            self.db.execute(
                select(RecommendationScoreCache)
                .where(
                    RecommendationScoreCache.user_id == user_id,
                    RecommendationScoreCache.algorithm_version == algorithm_version,
                )
                .order_by(
                    RecommendationScoreCache.rank_position.asc(),
                    RecommendationScoreCache.catalog_id.asc(),
                )
            )
            .scalars()
            .all()
        )
        return [_to_cached_record(item) for item in items]

    def get_cached_result_detail(
        self,
        *,
        user_id: str,
        catalog_id: str,
        algorithm_version: str | None = None,
    ) -> CachedRecommendationRecord | None:
        if algorithm_version is None:
            latest = self.get_cached_results(user_id=user_id)
            for cached_item in latest:
                if cached_item.catalog_id == catalog_id:
                    return cached_item
            return None

        row = self.db.get(
            RecommendationScoreCache,
            (user_id, catalog_id, algorithm_version),
        )
        if row is None:
            return None
        return _to_cached_record(row)

    def _lock_user(self, user_id: str) -> None:
        self.db.execute(
            select(User.id).where(User.id == user_id).with_for_update()
        ).scalar_one()


def _to_preference_entry(item: UserPreferenceMatrix) -> UserPreferenceVectorEntry:
    return UserPreferenceVectorEntry(
        user_id=item.user_id,
        feature_key=item.feature_key,
        source_layer=item.source_layer,
        raw_score=number_to_float(item.raw_score),
        preference_weight=number_to_float(item.preference_weight),
        preferred_min=number_to_float(item.preferred_min),
        preferred_max=number_to_float(item.preferred_max),
        updated_at=item.updated_at,
    )


def _to_cached_record(item: RecommendationScoreCache) -> CachedRecommendationRecord:
    return CachedRecommendationRecord(
        user_id=item.user_id,
        catalog_id=item.catalog_id,
        algorithm_version=item.algorithm_version,
        preference_match_score=number_to_float(item.preference_match_score)
        if hasattr(item, "preference_match_score")
        else number_to_float(item.content_score),
        rule_fit_score=number_to_float(item.rule_fit_score)
        if hasattr(item, "rule_fit_score")
        else number_to_float(item.rule_score),
        budget_fit_score=number_to_float(item.budget_fit_score)
        if hasattr(item, "budget_fit_score")
        else None,
        confidence_score=number_to_float(item.confidence_score)
        if hasattr(item, "confidence_score")
        else None,
        nlp_review_score=number_to_float(item.nlp_review_score)
        if hasattr(item, "nlp_review_score")
        else number_to_float(item.nlp_score),
        final_score=float(item.final_score),
        rank_position=item.rank_position,
        rationale=dict(item.rationale or {}),
        matrix_version=item.matrix_version if hasattr(item, "matrix_version") else None,
        feature_source_version=item.feature_source_version
        if hasattr(item, "feature_source_version")
        else None,
        generated_at=item.generated_at,
    )


def _matrix_by_source(
    entries: list[StringRecommendationMatrix],
) -> dict[str, dict[str, float | RecommendationFeatureSignalModel]]:
    grouped: dict[str, dict[str, float | RecommendationFeatureSignalModel]] = (
        defaultdict(dict)
    )
    for entry in entries:
        if entry.normalized_score is None:
            continue
        feature_key = _recommendation_feature_key(entry.feature_key)
        grouped[entry.source_layer][feature_key] = RecommendationFeatureSignalModel(
            normalized_score=float(str(entry.normalized_score)),
            confidence=number_to_float(entry.confidence),
            raw_value=number_to_float(entry.raw_value),
            evidence_note=entry.evidence_note,
            source_ref=entry.source_ref,
            source_version=entry.source_version,
            source_generated_at=entry.source_generated_at,
            review_count_snapshot=entry.review_count_snapshot,
        )
    return {source_layer: dict(values) for source_layer, values in grouped.items()}


def _recommendation_feature_key(feature_key: str) -> str:
    if feature_key == "attack":
        return "repulsion"
    return domain_feature_key(feature_key)


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value).__name__}")


def _required_float(values: dict[str, object], key: str) -> float:
    value = values[key]
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value for {key}")


def _required_int(values: dict[str, object], key: str) -> int:
    value = values[key]
    if isinstance(value, int | str):
        return int(value)
    raise TypeError(f"Expected integer value for {key}")


def _required_mapping(values: dict[str, object], key: str) -> dict[str, object]:
    value = values[key]
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"Expected mapping value for {key}")


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
