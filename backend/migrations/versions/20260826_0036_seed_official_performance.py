"""seed the reviewed official performance values for the approved cohort

Revision ID: 20260826_0036
Revises: 20260825_0035
Create Date: 2026-08-26 00:00:00

The admin-entered values are part of the canonical catalog seed so a fresh
database reproduces the reviewed 12-string runtime state. The removed
official-performance source URL is intentionally not restored.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from alembic import op


revision = "20260826_0036"
down_revision = "20260825_0035"
branch_labels = None
depends_on = None

PERFORMANCE_FIELDS = (
    "source_type",
    "source_name",
    "source_region",
    "category",
    "feature",
    "feel",
    "repulsion_power",
    "durability",
    "hitting_sound",
    "shock_absorption",
    "control",
    "notes",
)


def _seed_values() -> dict[str, dict[str, Any]]:
    source_path = (
        Path(__file__).resolve().parents[2] / "data" / "string_catalog_db_ready.json"
    )
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    values = payload.get("official_performance", {})
    if not isinstance(values, dict):
        return {}
    return {
        str(catalog_id): value
        for catalog_id, value in values.items()
        if isinstance(value, dict)
    }


def _row_params(catalog_id: str, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "catalog_id": catalog_id,
        **{field: values.get(field) for field in PERFORMANCE_FIELDS},
        "status": values.get("status", "manual_reviewed"),
    }


def upgrade() -> None:
    bind = op.get_bind()
    for catalog_id, values in _seed_values().items():
        params = _row_params(catalog_id, values)
        string_exists = bind.execute(
            sa.text("SELECT 1 FROM strings WHERE catalog_id = :catalog_id"),
            {"catalog_id": catalog_id},
        ).scalar()
        if string_exists is None:
            continue

        bind.execute(
            sa.text(
                """
                UPDATE strings
                SET official_performance_status = :status
                WHERE catalog_id = :catalog_id
                """
            ),
            params,
        )
        performance_exists = bind.execute(
            sa.text(
                "SELECT 1 FROM string_official_performance "
                "WHERE catalog_id = :catalog_id"
            ),
            {"catalog_id": catalog_id},
        ).scalar()
        if performance_exists is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO string_official_performance (
                        catalog_id, source_type, source_name, source_region,
                        category, feature, feel, repulsion_power, durability,
                        hitting_sound, shock_absorption, control, notes, status,
                        updated_at
                    ) VALUES (
                        :catalog_id, :source_type, :source_name, :source_region,
                        :category, :feature, :feel, :repulsion_power, :durability,
                        :hitting_sound, :shock_absorption, :control, :notes, :status,
                        CURRENT_TIMESTAMP
                    )
                    """
                ),
                params,
            )
            continue

        bind.execute(
            sa.text(
                """
                UPDATE string_official_performance
                SET source_type = :source_type,
                    source_name = :source_name,
                    source_region = :source_region,
                    category = :category,
                    feature = :feature,
                    feel = :feel,
                    repulsion_power = :repulsion_power,
                    durability = :durability,
                    hitting_sound = :hitting_sound,
                    shock_absorption = :shock_absorption,
                    control = :control,
                    notes = :notes,
                    status = :status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE catalog_id = :catalog_id
                """
            ),
            params,
        )


def downgrade() -> None:
    bind = op.get_bind()
    for catalog_id in _seed_values():
        bind.execute(
            sa.text(
                """
                UPDATE strings
                SET official_performance_status = 'pending_manual_fill'
                WHERE catalog_id = :catalog_id
                """
            ),
            {"catalog_id": catalog_id},
        )
        bind.execute(
            sa.text(
                """
                UPDATE string_official_performance
                SET source_type = NULL,
                    source_name = NULL,
                    source_region = NULL,
                    category = NULL,
                    feature = NULL,
                    feel = NULL,
                    repulsion_power = NULL,
                    durability = NULL,
                    hitting_sound = NULL,
                    shock_absorption = NULL,
                    control = NULL,
                    notes = NULL,
                    status = 'pending_manual_fill',
                    updated_at = CURRENT_TIMESTAMP
                WHERE catalog_id = :catalog_id
                """
            ),
            {"catalog_id": catalog_id},
        )
