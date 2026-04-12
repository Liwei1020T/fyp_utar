"""normalize string catalog

Revision ID: 20260412_0008
Revises: 20260411_0007
Create Date: 2026-04-12 12:00:00
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "20260412_0008"
down_revision = "20260411_0007"
branch_labels = None
depends_on = None


ASPECT_FIELDS = (
    "attack",
    "comfort",
    "control",
    "durability",
    "elasticity",
    "sound",
    "string_movement",
    "tension_retention",
    "value_for_money",
    "beginner_fit_score",
    "stability_score",
    "all_round_score",
)

FEATURE_DEFINITIONS = (
    ("attack", "Attack", "catalog_aspect", "score", 0, 1, "Explosive offensive response."),
    ("comfort", "Comfort", "catalog_aspect", "score", 0, 1, "Overall comfort and feel on impact."),
    ("control", "Control", "catalog_aspect", "score", 0, 1, "Control-oriented response."),
    ("durability", "Durability", "catalog_aspect", "score", 0, 1, "Resistance to snapping and wear."),
    ("elasticity", "Elasticity", "catalog_aspect", "score", 0, 1, "Elastic rebound feel."),
    ("sound", "Hitting Sound", "catalog_aspect", "score", 0, 1, "Crisp sound response."),
    ("string_movement", "String Movement", "catalog_aspect", "score", 0, 1, "String bed movement behaviour."),
    ("tension_retention", "Tension Retention", "catalog_aspect", "score", 0, 1, "Ability to hold tension over time."),
    ("value_for_money", "Value for Money", "catalog_aspect", "score", 0, 1, "Perceived value for price paid."),
    ("beginner_fit_score", "Beginner Fit", "derived_aspect", "score", 0, 1, "Derived beginner-friendliness score."),
    ("stability_score", "Stability", "derived_aspect", "score", 0, 1, "Derived stability score."),
    ("all_round_score", "All Round", "derived_aspect", "score", 0, 1, "Derived all-round playability score."),
    ("gauge_mm", "Gauge (mm)", "catalog_structured", "number", 0.5, 0.8, "Nominal string gauge."),
    ("skill_level_weight", "Skill Level Weight", "user_preference", "weight", 0, 1, "Weight derived from player skill level."),
    ("playing_style_weight", "Playing Style Weight", "user_preference", "weight", 0, 1, "Weight derived from playing style."),
    ("budget_weight", "Budget Weight", "user_preference", "weight", 0, 1, "Weight derived from budget fit."),
    ("durability_preference", "Durability Preference", "user_preference", "weight", 0, 1, "Player durability preference."),
    ("repulsion_preference", "Repulsion Preference", "user_preference", "weight", 0, 1, "Player repulsion preference."),
    ("control_preference", "Control Preference", "user_preference", "weight", 0, 1, "Player control preference."),
    ("sound_preference", "Sound Preference", "user_preference", "weight", 0, 1, "Player sound preference."),
    ("comfort_preference", "Comfort Preference", "user_preference", "weight", 0, 1, "Player comfort preference."),
)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _catalog_payload() -> dict[str, object]:
    path = _backend_root() / "data" / "string_catalog_db_ready.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_name(brand: str, model_name: str) -> str:
    return " ".join(
        f"{brand} {model_name}"
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_") or "legacy"


def _gauge_score(value: float | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, round((value - 0.58) / 0.14, 4)))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "string_catalog_items" in inspector.get_table_names():
        op.rename_table("string_catalog_items", "string_catalog_items_legacy")

    op.create_table(
        "brands",
        sa.Column("brand_code", sa.String(length=40), nullable=False),
        sa.Column("brand_name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("brand_code"),
        sa.UniqueConstraint("brand_name"),
    )
    op.create_index("ix_brands_brand_name", "brands", ["brand_name"], unique=True)

    op.create_table(
        "strings",
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("brand_code", sa.String(length=40), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("series_key", sa.String(length=80), nullable=True),
        sa.Column("series_label", sa.String(length=120), nullable=True),
        sa.Column("is_hybrid", sa.Boolean(), nullable=False),
        sa.Column("gauge_main_mm", sa.Numeric(4, 2), nullable=True),
        sa.Column("gauge_cross_mm", sa.Numeric(4, 2), nullable=True),
        sa.Column("gauge_label", sa.String(length=80), nullable=True),
        sa.Column("material_summary_en", sa.Text(), nullable=True),
        sa.Column("color_options_en", sa.JSON(), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=False),
        sa.Column("official_performance_status", sa.String(length=40), nullable=False),
        sa.Column("source_dataset_url", sa.Text(), nullable=True),
        sa.Column("source_language", sa.String(length=32), nullable=True),
        sa.Column("original_name", sa.String(length=160), nullable=True),
        sa.Column("original_brand_label", sa.String(length=160), nullable=True),
        sa.Column("original_series", sa.String(length=160), nullable=True),
        sa.Column("original_material", sa.Text(), nullable=True),
        sa.Column("original_color", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["brand_code"], ["brands.brand_code"]),
        sa.PrimaryKeyConstraint("catalog_id"),
        sa.UniqueConstraint("display_name"),
    )
    op.create_index("ix_strings_brand_code", "strings", ["brand_code"], unique=False)
    op.create_index("ix_strings_display_name", "strings", ["display_name"], unique=True)
    op.create_index("ix_strings_model_name", "strings", ["model_name"], unique=False)
    op.create_index("ix_strings_series_key", "strings", ["series_key"], unique=False)
    op.create_index(
        "ix_strings_official_performance_status",
        "strings",
        ["official_performance_status"],
        unique=False,
    )
    op.create_index("ix_strings_is_active", "strings", ["is_active"], unique=False)

    op.create_table(
        "string_catalog_metrics",
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("community_rating", sa.Numeric(4, 2), nullable=True),
        sa.Column("want_count", sa.Integer(), nullable=False),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["strings.catalog_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("catalog_id"),
    )

    op.create_table(
        "string_catalog_tags",
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("tag_key", sa.String(length=80), nullable=False),
        sa.Column("tag_label", sa.String(length=120), nullable=False),
        sa.Column("tag_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["catalog_id"], ["strings.catalog_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("catalog_id", "tag_key"),
    )

    op.create_table(
        "string_official_performance",
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=True),
        sa.Column("source_name", sa.String(length=160), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_region", sa.String(length=60), nullable=True),
        sa.Column("category", sa.Numeric(4, 2), nullable=True),
        sa.Column("feature", sa.Numeric(4, 2), nullable=True),
        sa.Column("feel", sa.Numeric(4, 2), nullable=True),
        sa.Column("repulsion_power", sa.Numeric(4, 2), nullable=True),
        sa.Column("durability", sa.Numeric(4, 2), nullable=True),
        sa.Column("hitting_sound", sa.Numeric(4, 2), nullable=True),
        sa.Column("shock_absorption", sa.Numeric(4, 2), nullable=True),
        sa.Column("control", sa.Numeric(4, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["strings.catalog_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("catalog_id"),
    )
    op.create_index(
        "ix_string_official_performance_status",
        "string_official_performance",
        ["status"],
        unique=False,
    )

    op.create_table(
        "inventory_items",
        sa.Column("inventory_id", sa.String(length=36), nullable=False),
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("sku", sa.String(length=120), nullable=True),
        sa.Column("current_stock", sa.Integer(), nullable=False),
        sa.Column("reserved_stock", sa.Integer(), nullable=False),
        sa.Column("available_stock", sa.Integer(), nullable=False),
        sa.Column("reorder_level", sa.Integer(), nullable=False),
        sa.Column("reorder_quantity", sa.Integer(), nullable=False),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("selling_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["strings.catalog_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("inventory_id"),
        sa.UniqueConstraint("catalog_id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_index("ix_inventory_items_catalog_id", "inventory_items", ["catalog_id"], unique=True)
    op.create_index("ix_inventory_items_is_active", "inventory_items", ["is_active"], unique=False)

    op.create_table(
        "inventory_movements",
        sa.Column("movement_id", sa.String(length=36), nullable=False),
        sa.Column("inventory_id", sa.String(length=36), nullable=False),
        sa.Column("movement_type", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(length=60), nullable=True),
        sa.Column("reference_id", sa.String(length=120), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventory_items.inventory_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("movement_id"),
    )
    op.create_index("ix_inventory_movements_inventory_id", "inventory_movements", ["inventory_id"], unique=False)
    op.create_index("ix_inventory_movements_movement_type", "inventory_movements", ["movement_type"], unique=False)
    op.create_index("ix_inventory_movements_created_at", "inventory_movements", ["created_at"], unique=False)

    op.create_table(
        "recommendation_feature_definitions",
        sa.Column("feature_key", sa.String(length=80), nullable=False),
        sa.Column("feature_label", sa.String(length=120), nullable=False),
        sa.Column("feature_group", sa.String(length=80), nullable=False),
        sa.Column("data_type", sa.String(length=32), nullable=False),
        sa.Column("min_value", sa.Numeric(6, 2), nullable=True),
        sa.Column("max_value", sa.Numeric(6, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("feature_key"),
    )
    op.create_index(
        "ix_recommendation_feature_definitions_feature_group",
        "recommendation_feature_definitions",
        ["feature_group"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_feature_definitions_is_active",
        "recommendation_feature_definitions",
        ["is_active"],
        unique=False,
    )

    op.create_table(
        "string_recommendation_matrix",
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("feature_key", sa.String(length=80), nullable=False),
        sa.Column("source_layer", sa.String(length=40), nullable=False),
        sa.Column("raw_value", sa.Numeric(8, 4), nullable=True),
        sa.Column("normalized_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 2), nullable=True),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["strings.catalog_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feature_key"], ["recommendation_feature_definitions.feature_key"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("catalog_id", "feature_key", "source_layer"),
    )
    op.create_index(
        "ix_string_recommendation_matrix_normalized_score",
        "string_recommendation_matrix",
        ["normalized_score"],
        unique=False,
    )

    op.create_table(
        "user_preference_matrix",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("feature_key", sa.String(length=80), nullable=False),
        sa.Column("source_layer", sa.String(length=40), nullable=False),
        sa.Column("preference_weight", sa.Numeric(6, 4), nullable=True),
        sa.Column("preferred_min", sa.Numeric(8, 4), nullable=True),
        sa.Column("preferred_max", sa.Numeric(8, 4), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["feature_key"], ["recommendation_feature_definitions.feature_key"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "feature_key", "source_layer"),
    )

    op.create_table(
        "recommendation_score_cache",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("algorithm_version", sa.String(length=80), nullable=False),
        sa.Column("content_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("collaborative_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("rule_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("nlp_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("final_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["strings.catalog_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "catalog_id", "algorithm_version"),
    )
    op.create_index(
        "ix_recommendation_score_cache_generated_at",
        "recommendation_score_cache",
        ["generated_at"],
        unique=False,
    )

    feature_table = sa.table(
        "recommendation_feature_definitions",
        sa.column("feature_key", sa.String),
        sa.column("feature_label", sa.String),
        sa.column("feature_group", sa.String),
        sa.column("data_type", sa.String),
        sa.column("min_value", sa.Numeric),
        sa.column("max_value", sa.Numeric),
        sa.column("description", sa.Text),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        feature_table,
        [
            {
                "feature_key": key,
                "feature_label": label,
                "feature_group": group,
                "data_type": data_type,
                "min_value": min_value,
                "max_value": max_value,
                "description": description,
                "is_active": True,
            }
            for key, label, group, data_type, min_value, max_value, description in FEATURE_DEFINITIONS
        ],
    )

    legacy_rows = []
    if "string_catalog_items_legacy" in sa.inspect(bind).get_table_names():
        legacy_rows = [
            dict(row._mapping)
            for row in bind.execute(
                sa.text(
                    """
                    SELECT
                        id,
                        brand,
                        model_name,
                        normalized_name,
                        price_rm,
                        attack,
                        comfort,
                        control,
                        durability,
                        elasticity,
                        sound,
                        string_movement,
                        tension_retention,
                        value_for_money,
                        beginner_fit_score,
                        stability_score,
                        all_round_score,
                        source_item_id,
                        source_url,
                        stock_level,
                        admin_note,
                        is_active,
                        created_at,
                        updated_at
                    FROM string_catalog_items_legacy
                    """
                )
            ).fetchall()
        ]
    legacy_by_normalized = {
        str(row["normalized_name"]).strip().lower(): row for row in legacy_rows
    }
    matched_legacy_ids: set[str] = set()

    payload = _catalog_payload()
    for brand in payload["brands"]:
        bind.execute(
            sa.text(
                """
                INSERT INTO brands (brand_code, brand_name)
                VALUES (:brand_code, :brand_name)
                ON CONFLICT (brand_code) DO NOTHING
                """
            ),
            brand,
        )

    for item in payload["strings"]:
        normalized_name = _normalize_name(item["brand_name"], item["model_name"])
        legacy = legacy_by_normalized.get(normalized_name)
        if legacy:
            matched_legacy_ids.add(str(legacy["id"]))
            bind.execute(
                sa.text(
                    "UPDATE bookings SET string_id = :new_id WHERE string_id = :old_id"
                ),
                {"new_id": item["catalog_id"], "old_id": legacy["id"]},
            )

        stock_level = int(legacy["stock_level"]) if legacy and legacy["stock_level"] is not None else 8
        price_rm = legacy["price_rm"] if legacy else None
        is_active = bool(legacy["is_active"]) if legacy else bool(item.get("is_active", True))
        inventory_id = str(legacy["id"]) if legacy else f"{item['catalog_id']}-inventory"

        bind.execute(
            sa.text(
                """
                INSERT INTO strings (
                    catalog_id, brand_code, display_name, model_name, series_key, series_label,
                    is_hybrid, gauge_main_mm, gauge_cross_mm, gauge_label, material_summary_en,
                    color_options_en, short_description, full_description, official_performance_status,
                    source_dataset_url, source_language, original_name, original_brand_label,
                    original_series, original_material, original_color, is_active,
                    created_at, updated_at
                )
                VALUES (
                    :catalog_id, :brand_code, :display_name, :model_name, :series_key, :series_label,
                    :is_hybrid, :gauge_main_mm, :gauge_cross_mm, :gauge_label, :material_summary_en,
                    :color_options_en, :short_description, :full_description, :official_performance_status,
                    :source_dataset_url, :source_language, :original_name, :original_brand_label,
                    :original_series, :original_material, :original_color, :is_active,
                    COALESCE(:created_at, CURRENT_TIMESTAMP), COALESCE(:updated_at, CURRENT_TIMESTAMP)
                )
                """
            ),
            {
                "catalog_id": item["catalog_id"],
                "brand_code": item["brand_code"],
                "display_name": item["display_name"],
                "model_name": item["model_name"],
                "series_key": item.get("series_key"),
                "series_label": item.get("series_label"),
                "is_hybrid": bool(item.get("is_hybrid", False)),
                "gauge_main_mm": item.get("gauge_main_mm"),
                "gauge_cross_mm": item.get("gauge_cross_mm"),
                "gauge_label": item.get("gauge_label"),
                "material_summary_en": item.get("material_summary_en"),
                "color_options_en": json.dumps(item.get("color_options_en") or []),
                "short_description": item["short_description"],
                "full_description": item["full_description"],
                "official_performance_status": item.get("official_performance_status", "pending_manual_fill"),
                "source_dataset_url": item.get("source_dataset_url"),
                "source_language": item.get("source_language", "en"),
                "original_name": item.get("original_name"),
                "original_brand_label": item.get("original_brand_label"),
                "original_series": item.get("original_series"),
                "original_material": item.get("original_material"),
                "original_color": item.get("original_color"),
                "is_active": is_active,
                "created_at": legacy["created_at"] if legacy else None,
                "updated_at": legacy["updated_at"] if legacy else None,
            },
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO string_catalog_metrics (
                    catalog_id, community_rating, want_count, used_count, review_count, updated_at
                )
                VALUES (
                    :catalog_id, :community_rating, :want_count, :used_count, :review_count,
                    COALESCE(:updated_at, CURRENT_TIMESTAMP)
                )
                """
            ),
            {
                "catalog_id": item["catalog_id"],
                "community_rating": item.get("community_rating"),
                "want_count": int(item.get("want_count", 0) or 0),
                "used_count": int(item.get("used_count", 0) or 0),
                "review_count": int(item.get("review_count", 0) or 0),
                "updated_at": legacy["updated_at"] if legacy else None,
            },
        )
        for tag in item.get("community_tags") or []:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO string_catalog_tags (catalog_id, tag_key, tag_label, tag_count)
                    VALUES (:catalog_id, :tag_key, :tag_label, :tag_count)
                    """
                ),
                {
                    "catalog_id": item["catalog_id"],
                    "tag_key": tag["tag_key"],
                    "tag_label": tag["tag_label"],
                    "tag_count": int(tag.get("tag_count", 0) or 0),
                },
            )
        bind.execute(
            sa.text(
                """
                INSERT INTO string_official_performance (
                    catalog_id, source_type, source_name, source_url, source_region,
                    category, feature, feel, repulsion_power, durability, hitting_sound,
                    shock_absorption, control, notes, status, updated_at
                )
                VALUES (
                    :catalog_id, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, :status, COALESCE(:updated_at, CURRENT_TIMESTAMP)
                )
                """
            ),
            {
                "catalog_id": item["catalog_id"],
                "status": item.get("official_performance_status", "pending_manual_fill"),
                "updated_at": legacy["updated_at"] if legacy else None,
            },
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO inventory_items (
                    inventory_id, catalog_id, sku, current_stock, reserved_stock, available_stock,
                    reorder_level, reorder_quantity, cost_price, selling_price, is_active, updated_at
                )
                VALUES (
                    :inventory_id, :catalog_id, :sku, :current_stock, :reserved_stock, :available_stock,
                    :reorder_level, :reorder_quantity, NULL, :selling_price, :is_active,
                    COALESCE(:updated_at, CURRENT_TIMESTAMP)
                )
                """
            ),
            {
                "inventory_id": inventory_id,
                "catalog_id": item["catalog_id"],
                "sku": f"STR-{str(item['brand_code']).upper()}-{re.sub(r'[^A-Z0-9]+', '-', str(item['model_name']).upper()).strip('-')}",
                "current_stock": stock_level,
                "reserved_stock": 0,
                "available_stock": stock_level,
                "reorder_level": 3,
                "reorder_quantity": 8,
                "selling_price": price_rm,
                "is_active": is_active,
                "updated_at": legacy["updated_at"] if legacy else None,
            },
        )
        if legacy and legacy.get("admin_note"):
            bind.execute(
                sa.text(
                    """
                    INSERT INTO inventory_movements (
                        movement_id, inventory_id, movement_type, quantity, reference_type,
                        reference_id, note, created_at
                    )
                    VALUES (
                        :movement_id, :inventory_id, 'ADJUSTMENT', :quantity, 'legacy_admin_note',
                        :reference_id, :note, COALESCE(:created_at, CURRENT_TIMESTAMP)
                    )
                    """
                ),
                {
                    "movement_id": f"{inventory_id}-note",
                    "inventory_id": inventory_id,
                    "quantity": stock_level,
                    "reference_id": legacy["id"],
                    "note": legacy["admin_note"],
                    "created_at": legacy["updated_at"],
                },
            )
        if legacy:
            for feature_key in ASPECT_FIELDS:
                bind.execute(
                    sa.text(
                        """
                        INSERT INTO string_recommendation_matrix (
                            catalog_id, feature_key, source_layer, raw_value, normalized_score,
                            confidence, evidence_note, source_ref, updated_at
                        )
                        VALUES (
                            :catalog_id, :feature_key, 'hybrid_derived', :raw_value, :normalized_score,
                            0.65, 'Backfilled from legacy flat catalog aspect scores.', :source_ref,
                            COALESCE(:updated_at, CURRENT_TIMESTAMP)
                        )
                        """
                    ),
                    {
                        "catalog_id": item["catalog_id"],
                        "feature_key": feature_key,
                        "raw_value": legacy.get(feature_key),
                        "normalized_score": legacy.get(feature_key),
                        "source_ref": legacy.get("source_url"),
                        "updated_at": legacy.get("updated_at"),
                    },
                )
        gauge_score = _gauge_score(item.get("gauge_main_mm"))
        if gauge_score is not None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO string_recommendation_matrix (
                        catalog_id, feature_key, source_layer, raw_value, normalized_score,
                        confidence, evidence_note, source_ref, updated_at
                    )
                    VALUES (
                        :catalog_id, 'gauge_mm', 'catalog_structured', :raw_value, :normalized_score,
                        0.90, 'Normalized directly from catalog gauge metadata.', :source_ref,
                        CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    "catalog_id": item["catalog_id"],
                    "raw_value": item.get("gauge_main_mm"),
                    "normalized_score": gauge_score,
                    "source_ref": item.get("source_dataset_url"),
                },
            )

    for legacy in legacy_rows:
        legacy_id = str(legacy["id"])
        if legacy_id in matched_legacy_ids:
            continue
        brand_code = _slug(str(legacy["brand"]))
        bind.execute(
            sa.text(
                """
                INSERT INTO brands (brand_code, brand_name)
                VALUES (:brand_code, :brand_name)
                ON CONFLICT (brand_code) DO NOTHING
                """
            ),
            {"brand_code": brand_code, "brand_name": legacy["brand"]},
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO strings (
                    catalog_id, brand_code, display_name, model_name, series_key, series_label,
                    is_hybrid, gauge_main_mm, gauge_cross_mm, gauge_label, material_summary_en,
                    color_options_en, short_description, full_description, official_performance_status,
                    source_dataset_url, source_language, original_name, original_brand_label,
                    original_series, original_material, original_color, is_active,
                    created_at, updated_at
                )
                VALUES (
                    :catalog_id, :brand_code, :display_name, :model_name, NULL, NULL,
                    0, NULL, NULL, NULL, NULL,
                    '[]', :short_description, :full_description, 'pending_manual_fill',
                    :source_url, 'legacy_migrated', :original_name, :original_brand_label,
                    NULL, NULL, NULL, :is_active, COALESCE(:created_at, CURRENT_TIMESTAMP),
                    COALESCE(:updated_at, CURRENT_TIMESTAMP)
                )
                """
            ),
            {
                "catalog_id": legacy_id,
                "brand_code": brand_code,
                "display_name": f"{legacy['brand']} {legacy['model_name']}",
                "model_name": legacy["model_name"],
                "short_description": f"Legacy migrated catalog entry for {legacy['brand']} {legacy['model_name']}.",
                "full_description": f"Legacy migrated catalog entry for {legacy['brand']} {legacy['model_name']}.",
                "source_url": legacy.get("source_url"),
                "original_name": legacy.get("model_name"),
                "original_brand_label": legacy.get("brand"),
                "is_active": bool(legacy.get("is_active", True)),
                "created_at": legacy.get("created_at"),
                "updated_at": legacy.get("updated_at"),
            },
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO string_catalog_metrics (
                    catalog_id, community_rating, want_count, used_count, review_count, updated_at
                )
                VALUES (:catalog_id, NULL, 0, 0, 0, COALESCE(:updated_at, CURRENT_TIMESTAMP))
                """
            ),
            {"catalog_id": legacy_id, "updated_at": legacy.get("updated_at")},
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO string_official_performance (
                    catalog_id, source_type, source_name, source_url, source_region,
                    category, feature, feel, repulsion_power, durability, hitting_sound,
                    shock_absorption, control, notes, status, updated_at
                )
                VALUES (
                    :catalog_id, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, 'pending_manual_fill', COALESCE(:updated_at, CURRENT_TIMESTAMP)
                )
                """
            ),
            {"catalog_id": legacy_id, "updated_at": legacy.get("updated_at")},
        )
        bind.execute(
            sa.text(
                """
                INSERT INTO inventory_items (
                    inventory_id, catalog_id, sku, current_stock, reserved_stock, available_stock,
                    reorder_level, reorder_quantity, cost_price, selling_price, is_active, updated_at
                )
                VALUES (
                    :inventory_id, :catalog_id, :sku, :current_stock, 0, :available_stock,
                    3, 8, NULL, :selling_price, :is_active, COALESCE(:updated_at, CURRENT_TIMESTAMP)
                )
                """
            ),
            {
                "inventory_id": legacy_id,
                "catalog_id": legacy_id,
                "sku": f"LEGACY-{legacy_id[:12].upper()}",
                "current_stock": int(legacy.get("stock_level") or 0),
                "available_stock": int(legacy.get("stock_level") or 0),
                "selling_price": legacy.get("price_rm"),
                "is_active": bool(legacy.get("is_active", True)),
                "updated_at": legacy.get("updated_at"),
            },
        )
        if legacy.get("admin_note"):
            bind.execute(
                sa.text(
                    """
                    INSERT INTO inventory_movements (
                        movement_id, inventory_id, movement_type, quantity, reference_type,
                        reference_id, note, created_at
                    )
                    VALUES (
                        :movement_id, :inventory_id, 'ADJUSTMENT', :quantity, 'legacy_admin_note',
                        :reference_id, :note, COALESCE(:created_at, CURRENT_TIMESTAMP)
                    )
                    """
                ),
                {
                    "movement_id": f"{legacy_id}-note",
                    "inventory_id": legacy_id,
                    "quantity": int(legacy.get("stock_level") or 0),
                    "reference_id": legacy_id,
                    "note": legacy.get("admin_note"),
                    "created_at": legacy.get("updated_at"),
                },
            )
        for feature_key in ASPECT_FIELDS:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO string_recommendation_matrix (
                        catalog_id, feature_key, source_layer, raw_value, normalized_score,
                        confidence, evidence_note, source_ref, updated_at
                    )
                    VALUES (
                        :catalog_id, :feature_key, 'hybrid_derived', :raw_value, :normalized_score,
                        0.65, 'Backfilled from legacy flat catalog aspect scores.', :source_ref,
                        COALESCE(:updated_at, CURRENT_TIMESTAMP)
                    )
                    """
                ),
                {
                    "catalog_id": legacy_id,
                    "feature_key": feature_key,
                    "raw_value": legacy.get(feature_key),
                    "normalized_score": legacy.get(feature_key),
                    "source_ref": legacy.get("source_url"),
                    "updated_at": legacy.get("updated_at"),
                },
            )

    booking_fks = [
        fk["name"]
        for fk in inspector.get_foreign_keys("bookings")
        if fk.get("referred_table") in {"string_catalog_items", "string_catalog_items_legacy"}
    ]
    with op.batch_alter_table("bookings", recreate="always") as batch_op:
        for constraint_name in booking_fks:
            if constraint_name:
                batch_op.drop_constraint(constraint_name, type_="foreignkey")
        batch_op.alter_column(
            "string_id",
            existing_type=sa.String(length=36),
            type_=sa.String(length=120),
            existing_nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_bookings_string_id_strings",
            "strings",
            ["string_id"],
            ["catalog_id"],
        )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the catalog normalization migration."
    )
