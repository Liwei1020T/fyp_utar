"""admin booking baseline

Revision ID: 20260404_0003
Revises: 20260404_0002
Create Date: 2026-04-04 02:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260404_0003"
down_revision = "20260404_0002"
branch_labels = None
depends_on = None


STATUS_REWRITES = (
    ("pending", "awaiting_dropoff"),
    ("confirmed", "awaiting_dropoff"),
    ("ready_for_pickup", "ready_for_collection"),
    ("picked_up", "completed"),
)


def upgrade() -> None:
    op.add_column(
        "booking_status_history",
        sa.Column("note", sa.Text(), nullable=True),
    )

    for old_status, new_status in STATUS_REWRITES:
        op.execute(
            sa.text(
                "UPDATE bookings SET status = :new_status WHERE status = :old_status"
            ).bindparams(old_status=old_status, new_status=new_status)
        )
        op.execute(
            sa.text(
                """
                UPDATE booking_status_history
                SET new_status = :new_status
                WHERE new_status = :old_status
                """
            ).bindparams(old_status=old_status, new_status=new_status)
        )
        op.execute(
            sa.text(
                """
                UPDATE booking_status_history
                SET old_status = :new_status
                WHERE old_status = :old_status
                """
            ).bindparams(old_status=old_status, new_status=new_status)
        )


def downgrade() -> None:
    for old_status, new_status in reversed(STATUS_REWRITES):
        op.execute(
            sa.text(
                "UPDATE bookings SET status = :old_status WHERE status = :new_status"
            ).bindparams(old_status=old_status, new_status=new_status)
        )
        op.execute(
            sa.text(
                """
                UPDATE booking_status_history
                SET new_status = :old_status
                WHERE new_status = :new_status
                """
            ).bindparams(old_status=old_status, new_status=new_status)
        )
        op.execute(
            sa.text(
                """
                UPDATE booking_status_history
                SET old_status = :old_status
                WHERE old_status = :new_status
                """
            ).bindparams(old_status=old_status, new_status=new_status)
        )

    op.drop_column("booking_status_history", "note")
