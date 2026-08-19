"""add durable booking conversation state

Revision ID: 20260723_0023
Revises: 20260723_0022
Create Date: 2026-07-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260723_0023"
down_revision = "20260723_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "booking_conversations" in sa.inspect(op.get_bind()).get_table_names():
        return

    op.create_table(
        "booking_conversations",
        sa.Column("booking_id", sa.String(length=36), nullable=False),
        sa.Column(
            "state",
            sa.String(length=20),
            server_default="waiting_admin",
            nullable=False,
        ),
        sa.Column(
            "support_requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "player_last_read_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "admin_last_read_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
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
        sa.CheckConstraint(
            "state IN ('waiting_admin', 'admin_joined', 'resolved', 'closed')",
            name="ck_booking_conversations_state",
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("booking_id"),
    )
    op.create_index(
        "ix_booking_conversations_state",
        "booking_conversations",
        ["state"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_booking_conversations_state",
        table_name="booking_conversations",
    )
    op.drop_table("booking_conversations")
