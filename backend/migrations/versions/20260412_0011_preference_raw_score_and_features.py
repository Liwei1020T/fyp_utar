"""preference raw score and live feature keys

Revision ID: 20260412_0011
Revises: 20260412_0010
Create Date: 2026-04-12 23:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260412_0011"
down_revision = "20260412_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user_preference_matrix") as batch_op:
        batch_op.add_column(sa.Column("raw_score", sa.Numeric(8, 4), nullable=True))

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
    bind = op.get_bind()
    existing_keys = {
        row[0]
        for row in bind.execute(
            sa.text("SELECT feature_key FROM recommendation_feature_definitions")
        )
    }
    rows = [
        {
            "feature_key": "repulsion",
            "feature_label": "Repulsion",
            "feature_group": "catalog_aspect",
            "data_type": "score",
            "min_value": 0,
            "max_value": 1,
            "description": "Power and rebound response.",
            "is_active": True,
        },
        {
            "feature_key": "sound",
            "feature_label": "Sound",
            "feature_group": "catalog_aspect",
            "data_type": "score",
            "min_value": 0,
            "max_value": 1,
            "description": "User-facing hitting sound response.",
            "is_active": True,
        },
    ]
    missing_rows = [row for row in rows if row["feature_key"] not in existing_keys]
    if missing_rows:
        op.bulk_insert(feature_table, missing_rows)


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the raw preference score migration."
    )
