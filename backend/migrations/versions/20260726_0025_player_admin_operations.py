"""complete player and admin operational records

Revision ID: 20260726_0025
Revises: 20260723_0024
Create Date: 2026-07-26 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260726_0025"
down_revision = "20260723_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    booking_columns = {item["name"] for item in inspector.get_columns("bookings")}
    if "service_method" not in booking_columns:
        op.add_column(
            "bookings",
            sa.Column(
                "service_method",
                sa.String(30),
                server_default="counter_dropoff",
                nullable=False,
            ),
        )

    feedback_columns = {
        item["name"] for item in inspector.get_columns("booking_feedback")
    }
    rating_columns = (
        "recommendation_relevance",
        "string_satisfaction",
        "tension_satisfaction",
        "comfort",
        "control",
        "repulsion",
        "durability",
    )
    for name in rating_columns:
        if name not in feedback_columns:
            op.add_column(
                "booking_feedback",
                sa.Column(name, sa.Integer(), nullable=True),
            )
    if "would_use_again" not in feedback_columns:
        op.add_column(
            "booking_feedback",
            sa.Column("would_use_again", sa.Boolean(), nullable=True),
        )
    if "comment" not in feedback_columns:
        op.add_column(
            "booking_feedback",
            sa.Column("comment", sa.Text(), nullable=True),
        )

    profile_columns = {item["name"] for item in inspector.get_columns("profiles")}
    if "privacy_settings" not in profile_columns:
        op.add_column(
            "profiles",
            sa.Column(
                "privacy_settings",
                sa.JSON(),
                server_default=sa.text("'{}'"),
                nullable=False,
            ),
        )

    store_setting_columns = {
        item["name"] for item in inspector.get_columns("store_settings")
    }
    if "default_service_price" not in store_setting_columns:
        op.add_column(
            "store_settings",
            sa.Column(
                "default_service_price",
                sa.Numeric(10, 2),
                server_default="0",
                nullable=False,
            ),
        )
    if "notification_settings" not in store_setting_columns:
        op.add_column(
            "store_settings",
            sa.Column(
                "notification_settings",
                sa.JSON(),
                server_default=sa.text("'{}'"),
                nullable=False,
            ),
        )

    if "device_tokens" not in existing_tables:
        op.create_table(
            "device_tokens",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("token", sa.String(255), nullable=False, unique=True),
            sa.Column("platform", sa.String(20), nullable=False),
            sa.Column("device_name", sa.String(120), nullable=True),
            sa.Column(
                "enabled", sa.Boolean(), nullable=False, server_default=sa.true()
            ),
            sa.Column(
                "last_seen_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_device_tokens_user_id", "device_tokens", ["user_id"])
        op.create_index("ix_device_tokens_token", "device_tokens", ["token"])
        op.create_index("ix_device_tokens_enabled", "device_tokens", ["enabled"])

    if "notifications" not in existing_tables:
        op.create_table(
            "notifications",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "device_token_id",
                sa.String(36),
                sa.ForeignKey("device_tokens.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("category", sa.String(30), nullable=False),
            sa.Column("title", sa.String(160), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("route", sa.String(255), nullable=True),
            sa.Column(
                "status", sa.String(20), nullable=False, server_default="pending"
            ),
            sa.Column("provider_message", sa.Text(), nullable=True),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
        op.create_index("ix_notifications_category", "notifications", ["category"])
        op.create_index("ix_notifications_status", "notifications", ["status"])

    if "check_in_tokens" not in existing_tables:
        op.create_table(
            "check_in_tokens",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "booking_id",
                sa.String(36),
                sa.ForeignKey("bookings.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_check_in_tokens_booking_id",
            "check_in_tokens",
            ["booking_id"],
        )
        op.create_index(
            "ix_check_in_tokens_token_hash",
            "check_in_tokens",
            ["token_hash"],
        )
        op.create_index(
            "ix_check_in_tokens_expires_at",
            "check_in_tokens",
            ["expires_at"],
        )

    if "account_deletion_requests" not in existing_tables:
        op.create_table(
            "account_deletion_requests",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "status", sa.String(20), nullable=False, server_default="pending"
            ),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column(
                "requested_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index(
            "ix_account_deletion_requests_user_id",
            "account_deletion_requests",
            ["user_id"],
        )
        op.create_index(
            "ix_account_deletion_requests_status",
            "account_deletion_requests",
            ["status"],
        )


def downgrade() -> None:
    op.drop_table("account_deletion_requests")
    op.drop_table("check_in_tokens")
    op.drop_table("notifications")
    op.drop_table("device_tokens")
    op.drop_column("store_settings", "notification_settings")
    op.drop_column("store_settings", "default_service_price")
    op.drop_column("profiles", "privacy_settings")
    op.drop_column("booking_feedback", "comment")
    op.drop_column("booking_feedback", "would_use_again")
    for name in (
        "durability",
        "repulsion",
        "control",
        "comfort",
        "tension_satisfaction",
        "string_satisfaction",
        "recommendation_relevance",
    ):
        op.drop_column("booking_feedback", name)
    op.drop_column("bookings", "service_method")
