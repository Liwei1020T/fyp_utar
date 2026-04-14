"""repair recommendation schema drift

Revision ID: 20260414_0016
Revises: 20260414_0015
Create Date: 2026-04-14 00:30:00
"""

from __future__ import annotations

from collections.abc import Iterable

from alembic import op
import sqlalchemy as sa


revision = "20260414_0016"
down_revision = "20260414_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _ensure_column(
        inspector,
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    _ensure_index(inspector, "users", "ix_users_is_active", ["is_active"])

    _ensure_column(
        inspector,
        "profiles",
        sa.Column("preferred_feel", sa.String(length=32), nullable=True),
    )
    _ensure_column(
        inspector,
        "profiles",
        sa.Column("recent_goal", sa.String(length=500), nullable=True),
    )

    _ensure_column(
        inspector,
        "string_recommendation_matrix",
        sa.Column("source_version", sa.String(length=80), nullable=True),
    )
    _ensure_column(
        inspector,
        "string_recommendation_matrix",
        sa.Column("source_generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    _ensure_column(
        inspector,
        "string_recommendation_matrix",
        sa.Column("review_count_snapshot", sa.Integer(), nullable=True),
    )

    _ensure_column(
        inspector,
        "recommendation_score_cache",
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=True),
    )
    _ensure_column(
        inspector,
        "recommendation_score_cache",
        sa.Column("matrix_version", sa.String(length=80), nullable=True),
    )
    _ensure_column(
        inspector,
        "recommendation_score_cache",
        sa.Column("feature_source_version", sa.String(length=80), nullable=True),
    )

    if "recommendation_runs" not in inspector.get_table_names():
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
        inspector = sa.inspect(bind)
    _ensure_index(
        inspector,
        "recommendation_runs",
        "ix_recommendation_runs_algorithm_version",
        ["algorithm_version"],
    )
    _ensure_index(
        inspector,
        "recommendation_runs",
        "ix_recommendation_runs_generated_at",
        ["generated_at"],
    )
    _ensure_index(
        inspector,
        "recommendation_runs",
        "ix_recommendation_runs_user_id",
        ["user_id"],
    )

    if "recommendation_run_items" not in inspector.get_table_names():
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
        inspector = sa.inspect(bind)
    _ensure_index(
        inspector,
        "recommendation_run_items",
        "ix_recommendation_run_items_catalog_id",
        ["catalog_id"],
    )
    _ensure_index(
        inspector,
        "recommendation_run_items",
        "ix_recommendation_run_items_run_id",
        ["run_id"],
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the recommendation schema repair migration."
    )


def _ensure_column(
    inspector: sa.Inspector,
    table_name: str,
    column: sa.Column[object],
) -> None:
    existing_columns = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name in existing_columns:
        return
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.add_column(column)


def _ensure_index(
    inspector: sa.Inspector,
    table_name: str,
    index_name: str,
    columns: Iterable[str],
) -> None:
    existing_indexes = {item["name"] for item in inspector.get_indexes(table_name)}
    if index_name in existing_indexes:
        return
    op.create_index(index_name, table_name, list(columns), unique=False)
