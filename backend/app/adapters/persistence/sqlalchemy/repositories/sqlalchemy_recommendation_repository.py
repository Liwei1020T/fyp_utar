from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection
from collections.abc import Mapping

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import BookingFeedback
from app.adapters.persistence.sqlalchemy.models import BookingStatusHistory
from app.adapters.persistence.sqlalchemy.models import Profile
from app.adapters.persistence.sqlalchemy.models import Racket
from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import StringInventoryItem
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.models import UserPreferenceMatrix
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_string_item
from app.domain.catalog.recommendation_features import domain_feature_key
from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import CommunityFeedbackRow
from app.domain.recommendation.entities import RecommendationFeatureSignalModel
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationInteraction
from app.domain.recommendation.entities import RacketRecommendationContext
from app.domain.recommendation.entities import UserPreferenceVectorEntry
from app.domain.recommendation.learning_signals import canonical_racket_model_key
from app.shared.serialization import number_to_float


class SqlAlchemyRecommendationRepository:
    def __init__(
        self,
        db: Session,
        approved_catalog_ids: Collection[str] | None = None,
    ) -> None:
        self.db = db
        self.approved_catalog_ids = (
            frozenset(approved_catalog_ids)
            if approved_catalog_ids is not None
            else None
        )

    def list_active_candidates(self) -> list[RecommendationCandidateModel]:
        query = (
            select(StringCatalogItem)
            .join(
                StringInventoryItem,
                StringInventoryItem.catalog_id == StringCatalogItem.catalog_id,
            )
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
            .where(
                StringCatalogItem.is_active.is_(True),
                StringInventoryItem.is_active.is_(True),
                StringInventoryItem.availability_status.in_(("in_stock", "low_stock")),
                StringInventoryItem.available_stock > 0,
            )
        )
        if self.approved_catalog_ids is not None:
            query = query.where(
                StringCatalogItem.catalog_id.in_(self.approved_catalog_ids)
            )
        items = (
            self.db.execute(
                query.order_by(
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

    def get_owned_racket_context(
        self,
        *,
        user_id: str,
        racket_id: str,
        target_tension: float,
    ) -> RacketRecommendationContext | None:
        racket = self.db.execute(
            select(Racket).where(Racket.id == racket_id, Racket.user_id == user_id)
        ).scalar_one_or_none()
        if racket is None:
            return None
        return RacketRecommendationContext(
            racket_id=racket.id,
            brand=racket.brand,
            model=racket.model,
            model_key=canonical_racket_model_key(racket.brand, racket.model),
            target_tension=target_tension,
        )

    def list_community_feedback_rows(self) -> list[CommunityFeedbackRow]:
        query = select(BookingFeedback, Booking).join(
            Booking, Booking.id == BookingFeedback.booking_id
        )
        if self.approved_catalog_ids is not None:
            query = query.where(Booking.string_id.in_(self.approved_catalog_ids))
        rows = self.db.execute(query).all()
        return [
            CommunityFeedbackRow(
                feedback_id=feedback.id,
                user_id=feedback.user_id,
                catalog_id=booking.string_id,
                racket_model_key=canonical_racket_model_key(
                    booking.racket_brand, booking.racket_model
                ),
                ratings={
                    "comfort": feedback.comfort,
                    "control": feedback.control,
                    "repulsion": feedback.repulsion,
                },
            )
            for feedback, booking in rows
            if booking.status == "completed"
        ]

    def list_recommendation_interactions(self) -> list[RecommendationInteraction]:
        completed_at = self._completed_at_subquery()
        query = (
            select(Booking, Profile, completed_at)
            .outerjoin(Profile, Profile.user_id == Booking.user_id)
            .where(Booking.status == "completed")
        )
        if self.approved_catalog_ids is not None:
            query = query.where(Booking.string_id.in_(self.approved_catalog_ids))
        rows = self.db.execute(query).all()
        interactions: list[RecommendationInteraction] = []
        for booking, profile, completed in rows:
            model_key = canonical_racket_model_key(
                booking.racket_brand, booking.racket_model
            )
            if model_key is None or completed is None:
                continue
            interactions.append(
                RecommendationInteraction(
                    booking_id=booking.id,
                    user_id=booking.user_id,
                    catalog_id=booking.string_id,
                    racket_id=booking.racket_id,
                    racket_model_key=model_key,
                    requested_tension=number_to_float(booking.requested_tension),
                    completed_at=completed,
                    preference_vector=_profile_preference_vector(profile),
                )
            )
        return interactions

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
            value_for_money = _float_or_none(result.get("value_for_money_score"))
            nlp_review_score = _float_or_none(result.get("nlp_review_score"))
            collaborative_score = _float_or_none(result.get("collaborative_score"))
            rationale = _required_mapping(result, "rationale")
            self.db.add(
                RecommendationScoreCache(
                    user_id=user_id,
                    catalog_id=str(result["catalog_id"]),
                    algorithm_version=algorithm_version,
                    content_score=preference_match,
                    collaborative_score=collaborative_score,
                    rule_score=rule_fit,
                    nlp_score=nlp_review_score,
                    preference_match_score=preference_match,
                    rule_fit_score=rule_fit,
                    value_for_money_score=value_for_money,
                    nlp_review_score=nlp_review_score,
                    final_score=_required_float(result, "final_score"),
                    rank_position=_required_int(result, "rank_position"),
                    rationale=rationale,
                )
            )
        self.db.flush()
        return self.get_cached_results(
            user_id=user_id,
            algorithm_version=algorithm_version,
        )

    def clear_score_cache(self, *, user_id: str) -> None:
        self._lock_user(user_id)
        self.db.execute(
            delete(RecommendationScoreCache).where(
                RecommendationScoreCache.user_id == user_id
            )
        )
        self.db.flush()

    def get_cached_results(
        self,
        *,
        user_id: str,
        algorithm_version: str | None = None,
    ) -> list[CachedRecommendationRecord]:
        base_query = self._sellable_cache_query()
        if algorithm_version is None:
            latest_query = base_query.where(RecommendationScoreCache.user_id == user_id)
            latest = (
                self.db.execute(
                    latest_query.order_by(
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

        query = base_query.where(
            RecommendationScoreCache.user_id == user_id,
            RecommendationScoreCache.algorithm_version == algorithm_version,
        )
        items = (
            self.db.execute(
                query.order_by(
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
        if (
            self.approved_catalog_ids is not None
            and catalog_id not in self.approved_catalog_ids
        ):
            return None
        if algorithm_version is None:
            latest = self.get_cached_results(user_id=user_id)
            for cached_item in latest:
                if cached_item.catalog_id == catalog_id:
                    return cached_item
            return None

        return next(
            (
                item
                for item in self.get_cached_results(
                    user_id=user_id,
                    algorithm_version=algorithm_version,
                )
                if item.catalog_id == catalog_id
            ),
            None,
        )

    def _sellable_cache_query(self):
        query = (
            select(RecommendationScoreCache)
            .join(
                StringCatalogItem,
                StringCatalogItem.catalog_id == RecommendationScoreCache.catalog_id,
            )
            .join(
                StringInventoryItem,
                StringInventoryItem.catalog_id == RecommendationScoreCache.catalog_id,
            )
            .where(
                StringCatalogItem.is_active.is_(True),
                StringInventoryItem.is_active.is_(True),
                StringInventoryItem.availability_status.in_(("in_stock", "low_stock")),
                StringInventoryItem.available_stock > 0,
            )
        )
        if self.approved_catalog_ids is not None:
            query = query.where(
                RecommendationScoreCache.catalog_id.in_(self.approved_catalog_ids)
            )
        return query

    def _lock_user(self, user_id: str) -> None:
        self.db.execute(
            select(User.id).where(User.id == user_id).with_for_update()
        ).scalar_one()

    @staticmethod
    def _completed_at_subquery():
        return (
            select(BookingStatusHistory.changed_at)
            .where(
                BookingStatusHistory.booking_id == Booking.id,
                BookingStatusHistory.new_status == "completed",
            )
            .order_by(BookingStatusHistory.changed_at.desc())
            .limit(1)
            .correlate(Booking)
            .scalar_subquery()
        )


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


def _profile_preference_vector(profile: Profile | None) -> tuple[int | None, ...]:
    if profile is None:
        return (None,) * 9
    return (
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
        value_for_money_score=number_to_float(item.value_for_money_score)
        if hasattr(item, "value_for_money_score")
        else None,
        nlp_review_score=number_to_float(item.nlp_review_score)
        if hasattr(item, "nlp_review_score")
        else number_to_float(item.nlp_score),
        final_score=float(item.final_score),
        rank_position=item.rank_position,
        rationale=dict(item.rationale or {}),
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
            raw_value=number_to_float(entry.raw_value),
            evidence_note=entry.evidence_note,
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
