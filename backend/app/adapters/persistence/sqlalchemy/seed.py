from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
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
from app.adapters.persistence.sqlalchemy.models import RacketModelCatalog
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.services.security.pbkdf2_password_hasher import Pbkdf2PasswordHasher
from app.config.settings import get_settings
from app.domain.auth.entities import AuthProvider
from app.domain.auth.entities import UserRole
from app.domain.recommendation.learning_signals import STANDARD_RACKET_MODELS
from app.shared.errors import ConflictError


logger = logging.getLogger(__name__)


STORE_SETTINGS_SEED_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "store_settings_seed.json"
)


def _load_store_seed() -> dict[str, Any]:
    payload = json.loads(STORE_SETTINGS_SEED_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Store settings seed must be a JSON object")
    if not isinstance(payload.get("store_settings"), dict):
        raise ValueError("Store settings seed is missing store_settings")
    if not isinstance(payload.get("business_hours"), dict):
        raise ValueError("Store settings seed is missing business_hours")
    return payload


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
    ensure_racket_model_catalog_seeded(db)
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
            if str(catalog_values["catalog_id"]) not in cohort_ids:
                continue
            inventory_values = dict(payload["inventory"])
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


def ensure_racket_model_catalog_seeded(db: Session) -> None:
    existing_keys = set(
        db.execute(select(RacketModelCatalog.model_key)).scalars().all()
    )
    for model_key, brand, model in STANDARD_RACKET_MODELS:
        if model_key in existing_keys:
            continue
        db.add(
            RacketModelCatalog(
                model_key=model_key,
                brand=brand,
                model=model,
                is_active=True,
            )
        )
    db.flush()


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
    seed = _load_store_seed()
    store_id = str(seed.get("store_id", "main"))
    business_hours_seed = seed["business_hours"]
    store_settings_seed = seed["store_settings"]

    business_hours = db.get(StoreBusinessHours, store_id)
    if business_hours is None:
        db.add(
            StoreBusinessHours(
                id=store_id,
                days_json=business_hours_seed["days"],
                special_closed_dates=business_hours_seed["special_closed_dates"],
            )
        )

    store_settings = db.get(StoreSettings, store_id)
    if store_settings is None:
        db.add(StoreSettings(id=store_id, **store_settings_seed))

    db.flush()
