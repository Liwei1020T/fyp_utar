"""fyp1 recommendation persistence alignment

Revision ID: 20260414_0015
Revises: 20260413_0014
Create Date: 2026-04-14 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260414_0015"
down_revision = "20260413_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )
        batch_op.create_index("ix_users_is_active", ["is_active"], unique=False)

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(
            sa.Column("budget_tier", sa.String(length=32), nullable=True)
        )
        batch_op.add_column(
            sa.Column("preferred_feel", sa.String(length=32), nullable=True)
        )
        batch_op.add_column(
            sa.Column("recent_goal", sa.String(length=500), nullable=True)
        )

    op.execute(
        sa.text(
            """
            UPDATE profiles
            SET budget_tier = CASE
                WHEN budget_max IS NOT NULL AND budget_max <= 30 THEN 'below_30'
                WHEN budget_min IS NOT NULL AND budget_min >= 50 THEN 'above_50'
                WHEN budget_min IS NOT NULL OR budget_max IS NOT NULL THEN 'between_30_50'
                ELSE budget_tier
            END
            WHERE budget_tier IS NULL
            """
        )
    )

    with op.batch_alter_table("string_recommendation_matrix") as batch_op:
        batch_op.add_column(
            sa.Column("source_version", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column("source_generated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("review_count_snapshot", sa.Integer(), nullable=True)
        )

    with op.batch_alter_table("recommendation_score_cache") as batch_op:
        batch_op.add_column(
            sa.Column("confidence_score", sa.Numeric(6, 4), nullable=True)
        )
        batch_op.add_column(
            sa.Column("matrix_version", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column("feature_source_version", sa.String(length=80), nullable=True)
        )

    with op.batch_alter_table("bookings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "expected_completion_datetime",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("collection_datetime", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("cancellation_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("completion_summary", sa.Text(), nullable=True))

    op.create_table(
        "recommendation_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("algorithm_version", sa.String(length=80), nullable=False),
        sa.Column("matrix_version", sa.String(length=80), nullable=True),
        sa.Column("feature_source_version", sa.String(length=80), nullable=True),
        sa.Column("request_snapshot", sa.JSON(), nullable=False),
        sa.Column("profile_snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_runs_algorithm_version",
        "recommendation_runs",
        ["algorithm_version"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_runs_generated_at",
        "recommendation_runs",
        ["generated_at"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_runs_user_id",
        "recommendation_runs",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "recommendation_run_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("catalog_id", sa.String(length=120), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("final_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("preference_match_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("rule_fit_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("budget_fit_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("nlp_review_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("score_breakdown", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["recommendation_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_run_items_catalog_id",
        "recommendation_run_items",
        ["catalog_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_run_items_run_id",
        "recommendation_run_items",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the FYP1 recommendation alignment migration."
    )
