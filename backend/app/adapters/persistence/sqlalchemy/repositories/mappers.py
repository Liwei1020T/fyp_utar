from __future__ import annotations

import json

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.models import Profile
from app.adapters.persistence.sqlalchemy.models import RecommendationLog
from app.adapters.persistence.sqlalchemy.models import StoreBusinessHours
from app.adapters.persistence.sqlalchemy.models import StoreSettings
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import User
from app.domain.auth.entities import PasswordResetCodeRecord
from app.domain.auth.entities import UserAccount
from app.domain.booking.entities import BookingRecord
from app.domain.booking.entities import BookingStatusHistoryEntry
from app.domain.booking.entities import BookingUpdateEntry
from app.domain.booking.policies import booking_order_code
from app.domain.profile.entities import PlayerProfile
from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationLogRecord
from app.domain.store.entities import BusinessHoursDay
from app.domain.store.entities import StoreBusinessHoursRecord
from app.domain.store.entities import StoreSettingsRecord
from app.shared.serialization import number_to_float


def to_user_account(user: User) -> UserAccount:
    return UserAccount(
        id=user.id,
        username=user.username,
        phone_number=user.phone_number,
        password_hash=user.password_hash,
        role=user.role,
        auth_provider=user.auth_provider,
        external_auth_id=user.external_auth_id,
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
        budget_min=number_to_float(profile.budget_min),
        budget_max=number_to_float(profile.budget_max),
        preferred_tension=number_to_float(profile.preferred_tension),
        game_type=profile.game_type,
        frequency_per_week=profile.frequency_per_week,
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
    return StringItem(
        id=item.id,
        brand=item.brand,
        model_name=item.model_name,
        normalized_name=item.normalized_name,
        price_rm=number_to_float(item.price_rm),
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
        stock_level=item.stock_level,
        admin_note=item.admin_note,
        is_active=item.is_active,
        created_at=item.created_at,
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
    return BookingRecord(
        id=booking.id,
        order_code=booking_order_code(booking.id),
        user_id=booking.user_id,
        string_id=booking.string_id,
        string_name=f"{booking.string_item.brand} {booking.string_item.model_name}",
        customer_phone_number=booking.user.phone_number if booking.user else None,
        customer_username=booking.user.username if booking.user else None,
        racket_brand=booking.racket_brand,
        racket_model=booking.racket_model,
        requested_tension=number_to_float(booking.requested_tension),
        drop_off_datetime=booking.drop_off_datetime,
        notes=booking.notes,
        status=booking.status,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        latest_admin_note=latest_admin_note,
        status_history=[
            BookingStatusHistoryEntry(
                old_status=entry.old_status,
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
        booking_notes=settings.booking_notes,
        store_policy_text=settings.store_policy_text,
        address=settings.address,
        updated_at=settings.updated_at.isoformat() if settings.updated_at else None,
    )


def to_recommendation_log(item: RecommendationLog) -> RecommendationLogRecord:
    return RecommendationLogRecord(
        id=item.id,
        user_id=item.user_id,
        phone_number=item.user.phone_number if item.user else None,
        username=item.user.username if item.user else None,
        request=json.loads(item.request_json),
        recommendation=json.loads(item.recommendation_json),
        algorithm_version=item.algorithm_version,
        created_at=item.created_at,
    )
