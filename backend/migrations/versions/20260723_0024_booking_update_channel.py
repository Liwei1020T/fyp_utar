"""distinguish conversation messages from service updates

Revision ID: 20260723_0024
Revises: 20260723_0023
Create Date: 2026-07-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260723_0024"
down_revision = "20260723_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_columns = {
        item["name"] for item in inspector.get_columns("booking_updates")
    }
    if "channel" in existing_columns:
        return

    op.add_column(
        "booking_updates",
        sa.Column(
            "channel",
            sa.String(length=20),
            server_default="service",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("booking_updates", "channel")
