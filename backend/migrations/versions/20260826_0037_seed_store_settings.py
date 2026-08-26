"""seed the configured single-store settings and business hours

Revision ID: 20260826_0037
Revises: 20260826_0036
Create Date: 2026-08-26 00:00:00

The checked-in store snapshot lets a rebuilt database start with the configured
shop profile and schedule. Existing rows are left untouched so a migration
cannot overwrite later admin edits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from alembic import op


revision = "20260826_0037"
down_revision = "20260826_0036"
branch_labels = None
depends_on = None


def _seed_values() -> dict[str, Any]:
    source_path = (
        Path(__file__).resolve().parents[2] / "data" / "store_settings_seed.json"
    )
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Store settings seed must be a JSON object")
    if not isinstance(payload.get("store_settings"), dict):
        raise ValueError("Store settings seed is missing store_settings")
    if not isinstance(payload.get("business_hours"), dict):
        raise ValueError("Store settings seed is missing business_hours")
    return payload


def _json_insert(statement: str, *names: str) -> sa.TextClause:
    return sa.text(statement).bindparams(
        *(sa.bindparam(name, type_=sa.JSON) for name in names)
    )


def upgrade() -> None:
    bind = op.get_bind()
    seed = _seed_values()
    store_id = str(seed.get("store_id", "main"))
    store_settings = seed["store_settings"]
    business_hours = seed["business_hours"]

    settings_exists = bind.execute(
        sa.text("SELECT 1 FROM store_settings WHERE id = :store_id"),
        {"store_id": store_id},
    ).scalar()
    if settings_exists is None:
        bind.execute(
            _json_insert(
                """
                INSERT INTO store_settings (
                    id, store_name, store_contact, support_text, payment_notes,
                    payment_qr_path, booking_notes, store_policy_text, address,
                    trending_string_ids, notification_settings,
                    created_at, updated_at
                ) VALUES (
                    :store_id, :store_name, :store_contact, :support_text,
                    :payment_notes, :payment_qr_path, :booking_notes,
                    :store_policy_text, :address, :trending_string_ids,
                    :notification_settings, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """,
                "trending_string_ids",
                "notification_settings",
            ),
            {
                "store_id": store_id,
                **store_settings,
            },
        )

    hours_exists = bind.execute(
        sa.text("SELECT 1 FROM store_business_hours WHERE id = :store_id"),
        {"store_id": store_id},
    ).scalar()
    if hours_exists is None:
        bind.execute(
            _json_insert(
                """
                INSERT INTO store_business_hours (
                    id, days_json, special_closed_dates, created_at, updated_at
                ) VALUES (
                    :store_id, :days_json, :special_closed_dates,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """,
                "days_json",
                "special_closed_dates",
            ),
            {
                "store_id": store_id,
                "days_json": business_hours["days"],
                "special_closed_dates": business_hours["special_closed_dates"],
            },
        )


def downgrade() -> None:
    # Seed data is intentionally preserved when rolling back the migration.
    pass
