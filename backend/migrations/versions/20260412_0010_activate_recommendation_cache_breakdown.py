"""activate recommendation cache breakdown

Revision ID: 20260412_0010
Revises: 20260412_0009
Create Date: 2026-04-12 22:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260412_0010"
down_revision = "20260412_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("recommendation_score_cache") as batch_op:
        batch_op.add_column(
            sa.Column("preference_match_score", sa.Numeric(6, 4), nullable=True)
        )
        batch_op.add_column(
            sa.Column("rule_fit_score", sa.Numeric(6, 4), nullable=True)
        )
        batch_op.add_column(
            sa.Column("budget_fit_score", sa.Numeric(6, 4), nullable=True)
        )
        batch_op.add_column(
            sa.Column("nlp_review_score", sa.Numeric(6, 4), nullable=True)
        )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE recommendation_score_cache
            SET
                preference_match_score = COALESCE(preference_match_score, content_score),
                rule_fit_score = COALESCE(rule_fit_score, rule_score),
                budget_fit_score = COALESCE(budget_fit_score, collaborative_score),
                nlp_review_score = COALESCE(nlp_review_score, nlp_score)
            """
        )
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
    existing = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM recommendation_feature_definitions
            WHERE feature_key = 'price_rm'
            """
        )
    ).first()
    if existing is None:
        op.bulk_insert(
            feature_table,
            [
                {
                    "feature_key": "price_rm",
                    "feature_label": "Price (RM)",
                    "feature_group": "catalog_structured",
                    "data_type": "number",
                    "min_value": 0,
                    "max_value": 999,
                    "description": "Current store selling price in MYR.",
                    "is_active": True,
                }
            ],
        )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the recommendation cache activation migration."
    )
