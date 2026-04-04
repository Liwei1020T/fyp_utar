"""store ops tables

Revision ID: 20260405_0005
Revises: 20260405_0004
Create Date: 2026-04-05 11:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0005"
down_revision = "20260405_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "store_business_hours",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("days_json", sa.JSON(), nullable=False),
        sa.Column("special_closed_dates", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "store_settings",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("store_name", sa.String(length=120), nullable=False),
        sa.Column("store_contact", sa.String(length=120), nullable=False),
        sa.Column("support_text", sa.Text(), nullable=False),
        sa.Column("payment_notes", sa.Text(), nullable=False),
        sa.Column("booking_notes", sa.Text(), nullable=False),
        sa.Column("store_policy_text", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("store_settings")
    op.drop_table("store_business_hours")
