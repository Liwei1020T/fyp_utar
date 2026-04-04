"""backend hardening cleanup

Revision ID: 20260331_0002
Revises: 20260330_0001
Create Date: 2026-03-31 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None

BOOKING_STATUSES = (
    "pending",
    "confirmed",
    "in_progress",
    "ready_for_pickup",
    "picked_up",
    "cancelled",
    "rejected",
)
USER_ROLES = ("customer", "admin")


def _quoted_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE bookings SET status = 'picked_up' WHERE status = 'completed'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE bookings SET status = 'in_progress' WHERE status = 'received'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET old_status = 'picked_up' WHERE old_status = 'completed'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET new_status = 'picked_up' WHERE new_status = 'completed'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET old_status = 'in_progress' WHERE old_status = 'received'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET new_status = 'in_progress' WHERE new_status = 'received'"
        )
    )

    with op.batch_alter_table("app_users") as batch_op:
        batch_op.drop_index("ix_app_users_email")
        batch_op.drop_column("email")
        batch_op.create_check_constraint(
            "ck_app_users_role_valid",
            f"role IN ({_quoted_values(USER_ROLES)})",
        )

    with op.batch_alter_table("customer_profiles") as batch_op:
        batch_op.add_column(sa.Column("sound_priority", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("tension_retention_priority", sa.Integer(), nullable=True)
        )

    with op.batch_alter_table("bookings") as batch_op:
        batch_op.create_check_constraint(
            "ck_bookings_status_valid",
            f"status IN ({_quoted_values(BOOKING_STATUSES)})",
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE bookings SET status = 'completed' WHERE status = 'picked_up'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE bookings SET status = 'cancelled' WHERE status = 'rejected'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET old_status = 'completed' WHERE old_status = 'picked_up'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET new_status = 'completed' WHERE new_status = 'picked_up'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET old_status = 'cancelled' WHERE old_status = 'rejected'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE booking_status_history "
            "SET new_status = 'cancelled' WHERE new_status = 'rejected'"
        )
    )

    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_constraint("ck_bookings_status_valid", type_="check")

    with op.batch_alter_table("customer_profiles") as batch_op:
        batch_op.drop_column("tension_retention_priority")
        batch_op.drop_column("sound_priority")

    with op.batch_alter_table("app_users") as batch_op:
        batch_op.drop_constraint("ck_app_users_role_valid", type_="check")
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_app_users_email", ["email"], unique=True)
