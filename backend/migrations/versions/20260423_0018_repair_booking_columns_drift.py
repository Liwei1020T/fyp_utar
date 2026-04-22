"""repair booking columns drift

Revision ID: 20260423_0018
Revises: 20260414_0017
Create Date: 2026-04-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260423_0018"
down_revision = "20260414_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_columns = {item["name"] for item in inspector.get_columns("bookings")}

    with op.batch_alter_table("bookings") as batch_op:
        if "expected_completion_datetime" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "expected_completion_datetime",
                    sa.DateTime(timezone=True),
                    nullable=True,
                )
            )
        if "collection_datetime" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "collection_datetime",
                    sa.DateTime(timezone=True),
                    nullable=True,
                )
            )
        if "cancellation_reason" not in existing_columns:
            batch_op.add_column(
                sa.Column("cancellation_reason", sa.Text(), nullable=True)
            )
        if "completion_summary" not in existing_columns:
            batch_op.add_column(
                sa.Column("completion_summary", sa.Text(), nullable=True)
            )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the booking drift repair migration."
    )
