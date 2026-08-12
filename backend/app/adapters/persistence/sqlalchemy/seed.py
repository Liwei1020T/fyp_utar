from __future__ import annotations

import logging
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.catalog_seed import approved_catalog_ids
from app.adapters.persistence.sqlalchemy.catalog_seed import seed_catalog_rows
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    ensure_recommendation_feature_definitions,
)
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    import_recommendation_matrix_csv,
)
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    normalize_legacy_feature_keys,
)
from app.adapters.persistence.sqlalchemy.models import Brand
from app.adapters.persistence.sqlalchemy.models import StoreBusinessHours
from app.adapters.persistence.sqlalchemy.models import StoreSettings
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import StringCatalogMetric
from app.adapters.persistence.sqlalchemy.models import StringCatalogTag
from app.adapters.persistence.sqlalchemy.models import StringInventoryItem
from app.adapters.persistence.sqlalchemy.models import StringOfficialPerformance
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.services.security.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.config.settings import get_settings
from app.domain.auth.entities import AuthProvider
from app.domain.auth.entities import UserRole
from app.shared.errors import ConflictError


logger = logging.getLogger(__name__)


DEFAULT_BUSINESS_HOURS_DAYS = [
    {
        "day": day,
        "is_open": False,
        "open_time": "09:00",
        "close_time": "17:00",
        "break_start": None,
        "break_end": None,
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 1,
    }
    for day in (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    )
]

DEFAULT_SPECIAL_CLOSED_DATES: list[str] = []

DEFAULT_STORE_SETTINGS = {
    "store_name": "StringSence",
    "store_contact": "Not configured",
    "support_text": (
        "Ask us about tension pairing, string feel, or drop-off timing and "
        "we will reply from the admin operations desk."
    ),
    "payment_notes": ("External payments require shop verification."),
    "booking_notes": (
        "Drop-off slots are generated from business hours and slot capacity settings."
    ),
    "store_policy_text": (
        "Reschedule or cancellation is allowed before the admin starts work on the racket."
    ),
    "address": "Not configured",
    "trending_string_ids": [],
    "default_service_price": 0,
    "notification_settings": {
        "booking": {"enabled": True},
        "payment": {"enabled": True},
        "service": {"enabled": True},
        "chat": {"enabled": True},
        "system": {"enabled": True},
    },
}


def ensure_seed_users(db: Session) -> None:
    settings = get_settings()
    if settings.seed_admin_enabled:
        ensure_seed_user(
            db,
            username=settings.seed_admin_username or "admin",
            phone_number=settings.seed_admin_phone_number or "",
            password=settings.seed_admin_password or "",
            role=UserRole.ADMIN.value,
        )


def ensure_seed_user(
    db: Session,
    *,
    username: str,
    phone_number: str,
    password: str,
    role: str,
) -> None:
    hasher = Pbkdf2PasswordHasher()
    normalized_phone = hasher.normalize_phone_number(phone_number)
    existing = db.execute(
        select(User).where(User.phone_number == normalized_phone)
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            User(
                username=username,
                phone_number=normalized_phone,
                password_hash=hasher.hash_password(password),
                role=role,
                auth_provider=AuthProvider.LOCAL.value,
            )
        )
        db.flush()
        return

    if existing.role != role:
        raise ConflictError(
            f"Seed {role} phone number is already assigned to a different role"
        )


def ensure_catalog_seeded(db: Session) -> None:
    settings = get_settings()
    ensure_recommendation_feature_definitions(db)
    normalize_legacy_feature_keys(db)
    db.flush()

    count = db.execute(select(func.count()).select_from(StringCatalogItem)).scalar_one()
    if count == 0:
        seed_rows = seed_catalog_rows(settings.approved_strings_path)
        cohort_ids = approved_catalog_ids(settings.approved_string_cohort_path)
        for brand in seed_rows["brands"]:
            db.merge(Brand(**brand))
        for payload in seed_rows["items"]:
            catalog_values = dict(payload["catalog"])
            inventory_values = dict(payload["inventory"])
            if str(catalog_values["catalog_id"]) not in cohort_ids:
                catalog_values["is_active"] = False
                inventory_values["is_active"] = False
                inventory_values["availability_status"] = "out_of_stock"
            item = StringCatalogItem(**catalog_values)
            item.metrics = StringCatalogMetric(
                catalog_id=item.catalog_id,
                **payload["metrics"],
            )
            item.tags = [
                StringCatalogTag(catalog_id=item.catalog_id, **tag)
                for tag in payload["tags"]
            ]
            item.official_performance = StringOfficialPerformance(
                **payload["official_performance"]
            )
            item.inventory_item = StringInventoryItem(**inventory_values)
            item.recommendation_entries = [
                StringRecommendationMatrix(
                    catalog_id=item.catalog_id,
                    **entry,
                )
                for entry in payload["matrix_entries"]
            ]
            db.add(item)
        db.flush()

    if settings.recommendation_matrix_path.is_file():
        _import_startup_recommendation_matrix(
            db,
            settings.recommendation_matrix_path,
        )


def _import_startup_recommendation_matrix(db: Session, source_path: Path) -> None:
    try:
        with db.begin_nested():
            import_recommendation_matrix_csv(db, source_path)
    except (BadZipFile, ElementTree.ParseError, OSError, ValueError) as error:
        logger.warning(
            "Recommendation matrix startup import skipped for %s: %s",
            source_path,
            error,
        )


def ensure_store_defaults(db: Session) -> None:
    business_hours = db.get(StoreBusinessHours, "main")
    if business_hours is None:
        db.add(
            StoreBusinessHours(
                id="main",
                days_json=DEFAULT_BUSINESS_HOURS_DAYS,
                special_closed_dates=DEFAULT_SPECIAL_CLOSED_DATES,
            )
        )

    store_settings = db.get(StoreSettings, "main")
    if store_settings is None:
        db.add(StoreSettings(id="main", **DEFAULT_STORE_SETTINGS))

    db.flush()
