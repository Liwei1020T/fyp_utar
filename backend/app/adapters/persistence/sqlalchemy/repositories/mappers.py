from __future__ import annotations

from typing import cast

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.models import Profile
from app.adapters.persistence.sqlalchemy.models import RecommendationRun
from app.adapters.persistence.sqlalchemy.models import RecommendationRunItem
from app.adapters.persistence.sqlalchemy.models import StoreBusinessHours
from app.adapters.persistence.sqlalchemy.models import StoreSettings
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import StringOfficialPerformance
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.models import User
from app.domain.auth.entities import PasswordResetCodeRecord
from app.domain.auth.entities import UserAccount
from app.domain.catalog.entities import RecommendationMatrixEntryRecord
from app.domain.booking.entities import BookingRecord
from app.domain.booking.entities import BookingStatusHistoryEntry
from app.domain.booking.entities import BookingUpdateEntry
from app.domain.catalog.recommendation_features import domain_feature_key
from app.domain.booking.policies import booking_order_code
from app.domain.catalog.entities import InventorySnapshot
from app.domain.catalog.entities import InventoryAvailabilityStatus
from app.domain.catalog.entities import InventoryPricingMode
from app.domain.catalog.entities import StringItem
from app.domain.catalog.entities import (
    StringOfficialPerformance as OfficialPerformanceRecord,
)
from app.domain.catalog.entities import StringTag
from app.domain.profile.entities import PlayerProfile
from app.domain.recommendation.entities import RecommendationRunItemRecord
from app.domain.recommendation.entities import RecommendationRunRecord
from app.domain.store.entities import BusinessHoursDay
from app.domain.store.entities import StoreBusinessHoursRecord
from app.domain.store.entities import StoreSettingsRecord
from app.shared.serialization import number_to_float


SOURCE_LAYER_PRIORITY = {
    "manual_rule": 0,
    "official_performance": 1,
    "nlp_review": 2,
    "hybrid_derived": 3,
    "feedback_signal": 4,
    "catalog_structured": 5,
}


def _normalize_pricing_mode(value: str | None) -> InventoryPricingMode:
    if value in {"fixed_price", "quoted_at_shop", "price_pending"}:
        return cast(InventoryPricingMode, value)
    return "price_pending"


def _normalize_availability_status(
    value: str | None,
    *,
    available_stock: int,
) -> InventoryAvailabilityStatus:
    if value in {"in_stock", "low_stock", "out_of_stock"}:
        return cast(InventoryAvailabilityStatus, value)
    if available_stock <= 0:
        return "out_of_stock"
    if available_stock <= 5:
        return "low_stock"
    return "in_stock"


def to_user_account(user: User) -> UserAccount:
    return UserAccount(
        id=user.id,
        username=user.username,
        phone_number=user.phone_number,
        password_hash=user.password_hash,
        auth_version=user.auth_version,
        role=user.role,
        auth_provider=user.auth_provider,
        external_auth_id=user.external_auth_id,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def to_password_reset_code(record: PasswordResetCode) -> PasswordResetCodeRecord:
    return PasswordResetCodeRecord(
        id=record.id,
        user_id=record.user_id,
        phone_number=record.phone_number,
        code_hash=record.code_hash,
        attempt_count=record.attempt_count,
        expires_at=record.expires_at,
        used_at=record.used_at,
        created_at=record.created_at,
    )


def to_profile(profile: Profile) -> PlayerProfile:
    return PlayerProfile(
        user_id=profile.user_id,
        skill_level=profile.skill_level,
        playing_style=profile.playing_style,
        preferred_tension=number_to_float(profile.preferred_tension),
        frequency_per_week=profile.frequency_per_week,
        preferred_feel=profile.preferred_feel,
        preferred_gauge=profile.preferred_gauge,
        recent_goal=profile.recent_goal,
        pref_attack=profile.pref_attack,
        pref_comfort=profile.pref_comfort,
        pref_control=profile.pref_control,
        pref_durability=profile.pref_durability,
        pref_elasticity=profile.pref_elasticity,
        pref_sound=profile.pref_sound,
        pref_string_movement=profile.pref_string_movement,
        pref_tension_retention=profile.pref_tension_retention,
        pref_value_for_money=profile.pref_value_for_money,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def to_string_item(item: StringCatalogItem) -> StringItem:
    inventory = item.inventory_item
    latest_note = None
    pricing_mode: InventoryPricingMode = "price_pending"
    availability_status: InventoryAvailabilityStatus = "out_of_stock"
    if inventory and inventory.movements:
        latest_note = next(
            (
                movement.note
                for movement in inventory.movements
                if movement.note and movement.note.strip()
            ),
            None,
        )
    if inventory is not None:
        pricing_mode = _normalize_pricing_mode(inventory.pricing_mode)
        availability_status = _normalize_availability_status(
            inventory.availability_status,
            available_stock=inventory.available_stock,
        )

    return StringItem(
        id=item.catalog_id,
        brand=item.brand_ref.brand_name,
        brand_code=item.brand_code,
        display_name=item.display_name,
        model_name=item.model_name,
        normalized_name=_normalized_name(item.brand_ref.brand_name, item.model_name),
        series_key=item.series_key,
        series_label=item.series_label,
        is_hybrid=item.is_hybrid,
        gauge_main_mm=number_to_float(item.gauge_main_mm),
        gauge_cross_mm=number_to_float(item.gauge_cross_mm),
        gauge_label=item.gauge_label,
        category=item.category,
        main_trait=item.main_trait,
        tension_min_lbs=item.tension_min_lbs,
        tension_max_lbs=item.tension_max_lbs,
        material_summary_en=item.material_summary_en,
        image_url=item.image_url,
        color_options_en=list(item.color_options_en or []),
        short_description=item.short_description,
        full_description=item.full_description,
        official_performance_status=item.official_performance_status,
        source_dataset_url=item.source_dataset_url,
        source_language=item.source_language,
        original_name=item.original_name,
        original_brand_label=item.original_brand_label,
        original_series=item.original_series,
        original_material=item.original_material,
        original_color=item.original_color,
        feedback_rating=number_to_float(item.metrics.feedback_rating)
        if item.metrics
        else None,
        want_count=item.metrics.want_count if item.metrics else 0,
        used_count=item.metrics.used_count if item.metrics else 0,
        review_count=item.metrics.review_count if item.metrics else 0,
        tags=[
            StringTag(
                tag_key=tag.tag_key,
                tag_label=tag.tag_label,
                tag_count=tag.tag_count,
            )
            for tag in item.tags
        ],
        official_performance=to_official_performance(item.official_performance),
        inventory=InventorySnapshot(
            inventory_id=inventory.inventory_id,
            current_stock=inventory.current_stock,
            reserved_stock=inventory.reserved_stock,
            available_stock=inventory.available_stock,
            reorder_level=inventory.reorder_level,
            reorder_quantity=inventory.reorder_quantity,
            cost_price=number_to_float(inventory.cost_price),
            selling_price=number_to_float(inventory.selling_price),
            pricing_mode=pricing_mode,
            availability_status=availability_status,
            is_active=inventory.is_active,
            latest_note=latest_note,
            updated_at=inventory.updated_at,
        )
        if inventory
        else None,
        aspect_scores=_collapsed_aspect_scores(item.recommendation_entries),
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def to_official_performance(
    item: StringOfficialPerformance | None,
) -> OfficialPerformanceRecord | None:
    if item is None:
        return None
    return OfficialPerformanceRecord(
        catalog_id=item.catalog_id,
        source_type=item.source_type,
        source_name=item.source_name,
        source_region=item.source_region,
        category=number_to_float(item.category),
        feature=number_to_float(item.feature),
        feel=number_to_float(item.feel),
        repulsion_power=number_to_float(item.repulsion_power),
        durability=number_to_float(item.durability),
        hitting_sound=number_to_float(item.hitting_sound),
        shock_absorption=number_to_float(item.shock_absorption),
        control=number_to_float(item.control),
        notes=item.notes,
        status=item.status,
        updated_at=item.updated_at,
    )


def to_booking_record(booking: Booking) -> BookingRecord:
    latest_admin_note = next(
        (
            entry.note
            for entry in reversed(list(booking.status_history))
            if entry.note and entry.note.strip()
        ),
        None,
    )
    string_name = _booking_string_name(booking)
    return BookingRecord(
        id=booking.id,
        order_code=booking_order_code(booking.id),
        user_id=booking.user_id,
        string_id=booking.string_id,
        string_name=string_name,
        racket_id=booking.racket_id,
        customer_phone_number=booking.user.phone_number if booking.user else None,
        customer_username=booking.user.username if booking.user else None,
        racket_brand=booking.racket_brand,
        racket_model=booking.racket_model,
        requested_tension=number_to_float(booking.requested_tension),
        drop_off_datetime=booking.drop_off_datetime,
        expected_completion_datetime=booking.expected_completion_datetime,
        collection_datetime=booking.collection_datetime,
        notes=booking.notes,
        service_method=booking.service_method,
        cancellation_reason=booking.cancellation_reason,
        completion_summary=booking.completion_summary,
        status=booking.status,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        latest_admin_note=latest_admin_note,
        status_history=[
            BookingStatusHistoryEntry(
                new_status=entry.new_status,
                changed_by_user_id=entry.changed_by_user_id,
                changed_by_phone_number=entry.changed_by.phone_number
                if entry.changed_by
                else None,
                note=entry.note,
                changed_at=entry.changed_at,
            )
            for entry in booking.status_history
        ],
        updates=[
            BookingUpdateEntry(
                id=entry.id,
                booking_id=entry.booking_id,
                author_user_id=entry.author_user_id,
                author_role=entry.author_role,
                author_phone_number=entry.author.phone_number if entry.author else None,
                comment=entry.comment,
                photo_path=entry.photo_path,
                photo_original_name=entry.photo_original_name,
                photo_content_type=entry.photo_content_type,
                photo_type=entry.photo_type,
                created_at=entry.created_at,
            )
            for entry in booking.updates
        ],
    )


def to_business_hours(hours: StoreBusinessHours) -> StoreBusinessHoursRecord:
    return StoreBusinessHoursRecord(
        id=hours.id,
        days=[
            BusinessHoursDay(
                day=str(day["day"]),
                is_open=bool(day["is_open"]),
                open_time=str(day["open_time"]),
                close_time=str(day["close_time"]),
                break_start=str(day["break_start"]) if day.get("break_start") else None,
                break_end=str(day["break_end"]) if day.get("break_end") else None,
                slot_duration_minutes=int(str(day["slot_duration_minutes"])),
                max_bookings_per_slot=int(str(day["max_bookings_per_slot"])),
            )
            for day in hours.days_json
        ],
        special_closed_dates=list(hours.special_closed_dates),
        updated_at=hours.updated_at.isoformat() if hours.updated_at else None,
    )


def to_store_settings(settings: StoreSettings) -> StoreSettingsRecord:
    return StoreSettingsRecord(
        id=settings.id,
        store_name=settings.store_name,
        store_contact=settings.store_contact,
        support_text=settings.support_text,
        payment_notes=settings.payment_notes,
        payment_qr_path=settings.payment_qr_path,
        booking_notes=settings.booking_notes,
        store_policy_text=settings.store_policy_text,
        address=settings.address,
        trending_string_ids=list(settings.trending_string_ids or []),
        notification_settings=dict(settings.notification_settings or {}),
        updated_at=settings.updated_at.isoformat() if settings.updated_at else None,
    )


def to_recommendation_run(item: RecommendationRun) -> RecommendationRunRecord:
    return RecommendationRunRecord(
        id=item.id,
        user_id=item.user_id,
        phone_number=item.user.phone_number if item.user else None,
        username=item.user.username if item.user else None,
        algorithm_version=item.algorithm_version,
        request_snapshot=dict(item.request_snapshot or {}),
        profile_snapshot=dict(item.profile_snapshot or {}),
        generated_at=item.generated_at,
        items=[to_recommendation_run_item(run_item) for run_item in item.items],
    )


def to_recommendation_run_item(
    item: RecommendationRunItem,
) -> RecommendationRunItemRecord:
    return RecommendationRunItemRecord(
        id=item.id,
        catalog_id=item.catalog_id,
        rank_position=item.rank_position,
        final_score=number_to_float(item.final_score) or 0.0,
        preference_match_score=number_to_float(item.preference_match_score),
        rule_fit_score=number_to_float(item.rule_fit_score),
        value_for_money_score=number_to_float(item.value_for_money_score),
        nlp_review_score=number_to_float(item.nlp_review_score),
        score_breakdown=dict(item.score_breakdown or {}),
        rationale=dict(item.rationale or {}),
    )


def _collapsed_aspect_scores(
    entries: list[StringRecommendationMatrix],
) -> dict[str, float]:
    selected: dict[str, tuple[int, float]] = {}
    for entry in entries:
        if entry.normalized_score is None:
            continue
        feature_key = domain_feature_key(entry.feature_key)
        priority = SOURCE_LAYER_PRIORITY.get(entry.source_layer, 99)
        score = float(entry.normalized_score)
        current = selected.get(feature_key)
        current_key = (priority, -score)
        if current is None or current_key < (current[0], -current[1]):
            selected[feature_key] = (priority, score)
    return {
        feature_key: round(score, 4) for feature_key, (_, score) in selected.items()
    }


def _normalized_name(brand_name: str, model_name: str) -> str:
    return " ".join(f"{brand_name} {model_name}".strip().lower().split())


def _booking_string_name(booking: Booking) -> str:
    if booking.string_item is not None:
        return booking.string_item.display_name
    return f"Archived string ({booking.string_id})"


def to_recommendation_matrix_entry(
    entry: StringRecommendationMatrix,
) -> RecommendationMatrixEntryRecord:
    definition = entry.feature_definition
    return RecommendationMatrixEntryRecord(
        catalog_id=entry.catalog_id,
        feature_key=entry.feature_key,
        feature_label=definition.feature_label if definition else None,
        feature_group=definition.feature_group if definition else None,
        source_layer=entry.source_layer,
        raw_value=number_to_float(entry.raw_value),
        normalized_score=number_to_float(entry.normalized_score),
        evidence_note=entry.evidence_note,
        updated_at=entry.updated_at,
    )
