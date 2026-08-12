"""remove recommendation confidence metadata

Revision ID: 20260812_0028
Revises: 20260811_0027
Create Date: 2026-08-12 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260812_0028"
down_revision = "20260811_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("string_recommendation_matrix") as batch_op:
        batch_op.drop_column("confidence")
        batch_op.drop_column("source_ref")
        batch_op.drop_column("source_version")
        batch_op.drop_column("source_generated_at")
        batch_op.drop_column("review_count_snapshot")

    with op.batch_alter_table("recommendation_score_cache") as batch_op:
        batch_op.drop_column("confidence_score")
        batch_op.drop_column("matrix_version")
        batch_op.drop_column("feature_source_version")

    with op.batch_alter_table("recommendation_runs") as batch_op:
        batch_op.drop_column("matrix_version")
        batch_op.drop_column("feature_source_version")

    with op.batch_alter_table("recommendation_run_items") as batch_op:
        batch_op.drop_column("confidence_score")


def downgrade() -> None:
    with op.batch_alter_table("recommendation_runs") as batch_op:
        batch_op.add_column(
            sa.Column("feature_source_version", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column("matrix_version", sa.String(length=80), nullable=True)
        )

    with op.batch_alter_table("recommendation_score_cache") as batch_op:
        batch_op.add_column(
            sa.Column("feature_source_version", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column("matrix_version", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column("confidence_score", sa.Numeric(6, 4), nullable=True)
        )

    with op.batch_alter_table("recommendation_run_items") as batch_op:
        batch_op.add_column(
            sa.Column("confidence_score", sa.Numeric(6, 4), nullable=True)
        )

    with op.batch_alter_table("string_recommendation_matrix") as batch_op:
        batch_op.add_column(
            sa.Column("review_count_snapshot", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("source_ref", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("source_version", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column("source_generated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("confidence", sa.Numeric(4, 2), nullable=True))
