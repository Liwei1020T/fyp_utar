"""booking update photo type

Revision ID: 20260411_0007
Revises: 20260407_0006
Create Date: 2026-04-11 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260411_0007"
down_revision = "20260407_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "booking_updates",
        sa.Column("photo_type", sa.String(length=40), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("booking_updates", "photo_type")
