from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from stringsense_backend.core.config import get_settings
from stringsense_backend.core.domain import AuthProvider
from stringsense_backend.core.domain import UserRole
from stringsense_backend.core.errors import ConflictError
from stringsense_backend.core.security import hash_password
from stringsense_backend.core.security import normalize_phone_number
from stringsense_backend.db.catalog_seed import approved_catalog_defaults
from stringsense_backend.db.models import StringCatalogItem
from stringsense_backend.db.models import User


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
    if settings.seed_vendor_enabled:
        ensure_seed_user(
            db,
            username=settings.seed_vendor_username or "vendor",
            phone_number=settings.seed_vendor_phone_number or "",
            password=settings.seed_vendor_password or "",
            role=UserRole.VENDOR.value,
        )


def ensure_seed_user(
    db: Session,
    *,
    username: str,
    phone_number: str,
    password: str,
    role: str,
) -> None:
    normalized_phone = normalize_phone_number(phone_number)
    existing = db.execute(
        select(User).where(User.phone_number == normalized_phone)
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            User(
                username=username,
                phone_number=normalized_phone,
                password_hash=hash_password(password),
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
    count = db.execute(select(func.count()).select_from(StringCatalogItem)).scalar_one()
    if count > 0:
        return

    for payload in approved_catalog_defaults(settings.approved_strings_path).values():
        db.add(StringCatalogItem(**payload))
    db.flush()
