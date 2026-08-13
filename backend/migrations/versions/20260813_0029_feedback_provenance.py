"""add feedback provenance and durability eligibility

Revision ID: 20260813_0029
Revises: 20260812_0028
Create Date: 2026-08-13 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260813_0029"
down_revision = "20260812_0028"
branch_labels = None
depends_on = None


DETAIL_RATING_CHECK = """
(recommendation_relevance IS NULL OR recommendation_relevance BETWEEN 1 AND 5)
AND (string_satisfaction IS NULL OR string_satisfaction BETWEEN 1 AND 5)
AND (tension_satisfaction IS NULL OR tension_satisfaction BETWEEN 1 AND 5)
AND (comfort IS NULL OR comfort BETWEEN 1 AND 5)
AND (control IS NULL OR control BETWEEN 1 AND 5)
AND (repulsion IS NULL OR repulsion BETWEEN 1 AND 5)
AND (durability IS NULL OR durability BETWEEN 1 AND 5)
"""


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns("booking_feedback")}
    if "durability_rated_at" not in columns:
        op.add_column(
            "booking_feedback",
            sa.Column("durability_rated_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "structured_field_confirmed_at" not in columns:
        op.add_column(
            "booking_feedback",
            sa.Column(
                "structured_field_confirmed_at",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
        )

    checks = {
        item["name"] for item in inspector.get_check_constraints("booking_feedback")
    }
    if "ck_booking_feedback_detail_ratings" not in checks:
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("booking_feedback") as batch_op:
                batch_op.create_check_constraint(
                    "ck_booking_feedback_detail_ratings",
                    DETAIL_RATING_CHECK,
                )
        else:
            op.create_check_constraint(
                "ck_booking_feedback_detail_ratings",
                "booking_feedback",
                DETAIL_RATING_CHECK,
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    checks = {
        item["name"] for item in inspector.get_check_constraints("booking_feedback")
    }
    if "ck_booking_feedback_detail_ratings" in checks:
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("booking_feedback") as batch_op:
                batch_op.drop_constraint(
                    "ck_booking_feedback_detail_ratings",
                    type_="check",
                )
        else:
            op.drop_constraint(
                "ck_booking_feedback_detail_ratings",
                "booking_feedback",
                type_="check",
            )
    columns = {item["name"] for item in inspector.get_columns("booking_feedback")}
    if "structured_field_confirmed_at" in columns:
        op.drop_column("booking_feedback", "structured_field_confirmed_at")
    if "durability_rated_at" in columns:
        op.drop_column("booking_feedback", "durability_rated_at")
