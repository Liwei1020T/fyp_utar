"""rename legacy catalog terminology to feedback

Revision ID: 20260831_0038
Revises: 20260826_0037
Create Date: 2026-08-31 00:00:00

The catalog metric and derived matrix values are renamed in place. Existing
ratings, tags, and descriptions are preserved; only their terminology changes.
Historical migration files remain immutable records of the old schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op


revision = "20260831_0038"
down_revision = "20260826_0037"
branch_labels = None
depends_on = None

OLD_METRIC_COLUMN = "community_rating"
NEW_METRIC_COLUMN = "feedback_rating"
OLD_SOURCE_LAYER = "community_signal"
NEW_SOURCE_LAYER = "feedback_signal"
OLD_DESCRIPTION_LABEL = "Community signals:"
NEW_DESCRIPTION_LABEL = "Feedback signals:"


def _rename_metric_column(*, downgrade: bool) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {
        column["name"] for column in inspector.get_columns("string_catalog_metrics")
    }
    old_column = NEW_METRIC_COLUMN if downgrade else OLD_METRIC_COLUMN
    new_column = OLD_METRIC_COLUMN if downgrade else NEW_METRIC_COLUMN
    if old_column not in columns or new_column in columns:
        return

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("string_catalog_metrics") as batch_op:
            batch_op.alter_column(old_column, new_column_name=new_column)
    else:
        op.alter_column(
            "string_catalog_metrics",
            old_column,
            new_column_name=new_column,
        )


def _catalog_seed() -> list[dict[str, object]]:
    source = (
        Path(__file__).resolve().parents[2] / "data" / "string_catalog_db_ready.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("strings") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _backfill_feedback_seed() -> None:
    bind = op.get_bind()
    for row in _catalog_seed():
        catalog_id = row.get("catalog_id")
        if not catalog_id:
            continue
        feedback_rating = row.get(NEW_METRIC_COLUMN)
        if feedback_rating is not None:
            bind.execute(
                sa.text(
                    """
                    UPDATE string_catalog_metrics
                    SET feedback_rating = COALESCE(feedback_rating, :feedback_rating)
                    WHERE catalog_id = :catalog_id
                    """
                ),
                {
                    "catalog_id": str(catalog_id),
                    "feedback_rating": feedback_rating,
                },
            )
        for tag in row.get("feedback_tags") or []:
            if not isinstance(tag, dict) or not tag.get("tag_key"):
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO string_catalog_tags (
                        catalog_id, tag_key, tag_label, tag_count
                    )
                    VALUES (:catalog_id, :tag_key, :tag_label, :tag_count)
                    ON CONFLICT (catalog_id, tag_key) DO NOTHING
                    """
                ),
                {
                    "catalog_id": str(catalog_id),
                    "tag_key": str(tag["tag_key"]),
                    "tag_label": str(tag.get("tag_label") or tag["tag_key"]),
                    "tag_count": int(tag.get("tag_count", 0) or 0),
                },
            )


def upgrade() -> None:
    _rename_metric_column(downgrade=False)
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE string_recommendation_matrix "
            "SET source_layer = :new_layer WHERE source_layer = :old_layer"
        ),
        {"old_layer": OLD_SOURCE_LAYER, "new_layer": NEW_SOURCE_LAYER},
    )
    bind.execute(
        sa.text(
            "UPDATE strings SET full_description = replace(full_description, :old, :new)"
        ),
        {"old": OLD_DESCRIPTION_LABEL, "new": NEW_DESCRIPTION_LABEL},
    )
    _backfill_feedback_seed()


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE string_recommendation_matrix "
            "SET source_layer = :old_layer WHERE source_layer = :new_layer"
        ),
        {"old_layer": OLD_SOURCE_LAYER, "new_layer": NEW_SOURCE_LAYER},
    )
    bind.execute(
        sa.text(
            "UPDATE strings SET full_description = replace(full_description, :old, :new)"
        ),
        {"old": NEW_DESCRIPTION_LABEL, "new": OLD_DESCRIPTION_LABEL},
    )
    _rename_metric_column(downgrade=True)
