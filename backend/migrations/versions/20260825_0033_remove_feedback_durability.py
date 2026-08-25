"""remove durability from player feedback

Revision ID: 20260825_0033
Revises: 20260818_0032
Create Date: 2026-08-25 00:00:00

The old feedback durability values and field-level confirmation metadata are
intentionally discarded. Product catalogue durability and player preference
durability remain separate fields.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260825_0033"
down_revision = "20260818_0032"
branch_labels = None
depends_on = None

CHECK_NAME = "ck_booking_feedback_detail_ratings"
PROVENANCE_COLUMN = "structured_field_confirmed_at"
CHECK_WITHOUT_DURABILITY = """
    (recommendation_relevance IS NULL OR recommendation_relevance BETWEEN 1 AND 5)
    AND (string_satisfaction IS NULL OR string_satisfaction BETWEEN 1 AND 5)
    AND (tension_satisfaction IS NULL OR tension_satisfaction BETWEEN 1 AND 5)
    AND (comfort IS NULL OR comfort BETWEEN 1 AND 5)
    AND (control IS NULL OR control BETWEEN 1 AND 5)
    AND (repulsion IS NULL OR repulsion BETWEEN 1 AND 5)
"""
CHECK_WITH_DURABILITY = f"""
    {CHECK_WITHOUT_DURABILITY}
    AND (durability IS NULL OR durability BETWEEN 1 AND 5)
"""


def _alter_feedback_table(*, restoring_durability: bool) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("booking_feedback")}
    checks = {
        check["name"] for check in inspector.get_check_constraints("booking_feedback")
    }
    check_sql = (
        CHECK_WITH_DURABILITY if restoring_durability else CHECK_WITHOUT_DURABILITY
    )

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("booking_feedback") as batch_op:
            if CHECK_NAME in checks:
                batch_op.drop_constraint(CHECK_NAME, type_="check")
            if restoring_durability:
                if "durability" not in columns:
                    batch_op.add_column(
                        sa.Column("durability", sa.Integer(), nullable=True)
                    )
                if "durability_rated_at" not in columns:
                    batch_op.add_column(
                        sa.Column(
                            "durability_rated_at",
                            sa.DateTime(timezone=True),
                            nullable=True,
                        )
                    )
                if PROVENANCE_COLUMN not in columns:
                    batch_op.add_column(
                        sa.Column(
                            PROVENANCE_COLUMN,
                            sa.JSON(),
                            nullable=False,
                            server_default=sa.text("'{}'"),
                        )
                    )
            else:
                if "durability_rated_at" in columns:
                    batch_op.drop_column("durability_rated_at")
                if "durability" in columns:
                    batch_op.drop_column("durability")
                if PROVENANCE_COLUMN in columns:
                    batch_op.drop_column(PROVENANCE_COLUMN)
            batch_op.create_check_constraint(CHECK_NAME, check_sql)
        return

    if CHECK_NAME in checks:
        op.drop_constraint(CHECK_NAME, "booking_feedback", type_="check")
    if restoring_durability:
        if "durability" not in columns:
            op.add_column(
                "booking_feedback", sa.Column("durability", sa.Integer(), nullable=True)
            )
        if "durability_rated_at" not in columns:
            op.add_column(
                "booking_feedback",
                sa.Column(
                    "durability_rated_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
            )
        if PROVENANCE_COLUMN not in columns:
            op.add_column(
                "booking_feedback",
                sa.Column(
                    PROVENANCE_COLUMN,
                    sa.JSON(),
                    nullable=False,
                    server_default=sa.text("'{}'"),
                ),
            )
    else:
        if "durability_rated_at" in columns:
            op.drop_column("booking_feedback", "durability_rated_at")
        if "durability" in columns:
            op.drop_column("booking_feedback", "durability")
        if PROVENANCE_COLUMN in columns:
            op.drop_column("booking_feedback", PROVENANCE_COLUMN)
    op.create_check_constraint(CHECK_NAME, "booking_feedback", check_sql)


def upgrade() -> None:
    _alter_feedback_table(restoring_durability=False)


def downgrade() -> None:
    _alter_feedback_table(restoring_durability=True)
