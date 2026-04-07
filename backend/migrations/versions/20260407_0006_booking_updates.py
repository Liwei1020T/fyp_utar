"""booking updates

Revision ID: 20260407_0006
Revises: 20260405_0005
Create Date: 2026-04-07 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260407_0006"
down_revision = "20260405_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booking_updates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("booking_id", sa.String(length=36), nullable=False),
        sa.Column("author_user_id", sa.String(length=36), nullable=False),
        sa.Column("author_role", sa.String(length=20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("photo_path", sa.Text(), nullable=True),
        sa.Column("photo_original_name", sa.String(length=255), nullable=True),
        sa.Column("photo_content_type", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_booking_updates_author_user_id"),
        "booking_updates",
        ["author_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_booking_updates_booking_id"),
        "booking_updates",
        ["booking_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_booking_updates_booking_id"), table_name="booking_updates")
    op.drop_index(
        op.f("ix_booking_updates_author_user_id"), table_name="booking_updates"
    )
    op.drop_table("booking_updates")
