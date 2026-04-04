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
from stringsense_backend.db.models import StoreBusinessHours
from stringsense_backend.db.models import StoreSettings
from stringsense_backend.db.models import User


DEFAULT_BUSINESS_HOURS_DAYS = [
    {
        "day": "Monday",
        "is_open": True,
        "open_time": "11:00",
        "close_time": "20:00",
        "break_start": "15:00",
        "break_end": "16:00",
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 3,
    },
    {
        "day": "Tuesday",
        "is_open": True,
        "open_time": "11:00",
        "close_time": "20:00",
        "break_start": "15:00",
        "break_end": "16:00",
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 3,
    },
    {
        "day": "Wednesday",
        "is_open": True,
        "open_time": "11:00",
        "close_time": "20:00",
        "break_start": "15:00",
        "break_end": "16:00",
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 3,
    },
    {
        "day": "Thursday",
        "is_open": True,
        "open_time": "11:00",
        "close_time": "21:00",
        "break_start": "15:00",
        "break_end": "16:00",
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 3,
    },
    {
        "day": "Friday",
        "is_open": True,
        "open_time": "11:00",
        "close_time": "21:00",
        "break_start": "15:00",
        "break_end": "16:00",
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 4,
    },
    {
        "day": "Saturday",
        "is_open": True,
        "open_time": "10:00",
        "close_time": "21:00",
        "break_start": "14:00",
        "break_end": "15:00",
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 4,
    },
    {
        "day": "Sunday",
        "is_open": True,
        "open_time": "10:00",
        "close_time": "18:00",
        "break_start": "13:30",
        "break_end": "14:30",
        "slot_duration_minutes": 30,
        "max_bookings_per_slot": 3,
    },
]

DEFAULT_SPECIAL_CLOSED_DATES = ["2026-04-14"]

DEFAULT_STORE_SETTINGS = {
    "store_name": "Apex String Lab",
    "store_contact": "+60 12-999 4421",
    "support_text": (
        "Ask us about tension pairing, string feel, or drop-off timing and "
        "we will reply from the admin operations desk."
    ),
    "payment_notes": (
        "Full payment is required to confirm every booking in this FYP prototype."
    ),
    "booking_notes": (
        "Drop-off slots are generated from business hours and slot capacity settings."
    ),
    "store_policy_text": (
        "Reschedule and cancellation are allowed only before payment is completed."
    ),
    "address": "Level 2, Jalil Sports Hub, Bukit Jalil, Kuala Lumpur",
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
