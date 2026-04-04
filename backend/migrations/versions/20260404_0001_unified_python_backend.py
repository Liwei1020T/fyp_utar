"""unified python backend

Revision ID: 20260404_0001
Revises:
Create Date: 2026-04-04 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260404_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("auth_provider", sa.String(length=40), nullable=False),
        sa.Column("external_auth_id", sa.String(length=64), nullable=True),
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
        sa.UniqueConstraint("external_auth_id"),
        sa.UniqueConstraint("phone_number"),
    )
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("skill_level", sa.String(length=32), nullable=True),
        sa.Column("playing_style", sa.String(length=32), nullable=True),
        sa.Column("budget_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("preferred_tension", sa.Numeric(4, 1), nullable=True),
        sa.Column("game_type", sa.String(length=16), nullable=True),
        sa.Column("frequency_per_week", sa.Integer(), nullable=True),
        sa.Column("pref_attack", sa.Integer(), nullable=True),
        sa.Column("pref_comfort", sa.Integer(), nullable=True),
        sa.Column("pref_control", sa.Integer(), nullable=True),
        sa.Column("pref_durability", sa.Integer(), nullable=True),
        sa.Column("pref_elasticity", sa.Integer(), nullable=True),
        sa.Column("pref_sound", sa.Integer(), nullable=True),
        sa.Column("pref_string_movement", sa.Integer(), nullable=True),
        sa.Column("pref_tension_retention", sa.Integer(), nullable=True),
        sa.Column("pref_value_for_money", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"], unique=True)

    op.create_table(
        "string_catalog_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("price_rm", sa.Numeric(10, 2), nullable=True),
        sa.Column("attack", sa.Numeric(4, 2), nullable=False),
        sa.Column("comfort", sa.Numeric(4, 2), nullable=False),
        sa.Column("control", sa.Numeric(4, 2), nullable=False),
        sa.Column("durability", sa.Numeric(4, 2), nullable=False),
        sa.Column("elasticity", sa.Numeric(4, 2), nullable=False),
        sa.Column("sound", sa.Numeric(4, 2), nullable=False),
        sa.Column("string_movement", sa.Numeric(4, 2), nullable=False),
        sa.Column("tension_retention", sa.Numeric(4, 2), nullable=False),
        sa.Column("value_for_money", sa.Numeric(4, 2), nullable=False),
        sa.Column("beginner_fit_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("stability_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("all_round_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("source_item_id", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.UniqueConstraint("normalized_name"),
    )
    op.create_index(
        "ix_string_catalog_items_brand",
        "string_catalog_items",
        ["brand"],
        unique=False,
    )
    op.create_index(
        "ix_string_catalog_items_model_name",
        "string_catalog_items",
        ["model_name"],
        unique=False,
    )
    op.create_index(
        "ix_string_catalog_items_normalized_name",
        "string_catalog_items",
        ["normalized_name"],
        unique=True,
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("string_id", sa.String(length=36), nullable=False),
        sa.Column("racket_brand", sa.String(length=100), nullable=True),
        sa.Column("racket_model", sa.String(length=100), nullable=True),
        sa.Column("requested_tension", sa.Numeric(4, 1), nullable=True),
        sa.Column("drop_off_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
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
        sa.ForeignKeyConstraint(["string_id"], ["string_catalog_items.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_status", "bookings", ["status"], unique=False)
    op.create_index("ix_bookings_string_id", "bookings", ["string_id"], unique=False)
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"], unique=False)

    op.create_table(
        "booking_status_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("booking_id", sa.String(length=36), nullable=False),
        sa.Column("old_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=False),
        sa.Column("changed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_booking_status_history_booking_id",
        "booking_status_history",
        ["booking_id"],
        unique=False,
    )

    op.create_table(
        "recommendation_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("request_json", sa.Text(), nullable=False),
        sa.Column("recommendation_json", sa.Text(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_logs_algorithm_version",
        "recommendation_logs",
        ["algorithm_version"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_logs_user_id",
        "recommendation_logs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_logs_user_id", table_name="recommendation_logs")
    op.drop_index(
        "ix_recommendation_logs_algorithm_version",
        table_name="recommendation_logs",
    )
    op.drop_table("recommendation_logs")
    op.drop_index(
        "ix_booking_status_history_booking_id",
        table_name="booking_status_history",
    )
    op.drop_table("booking_status_history")
    op.drop_index("ix_bookings_user_id", table_name="bookings")
    op.drop_index("ix_bookings_string_id", table_name="bookings")
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index(
        "ix_string_catalog_items_normalized_name",
        table_name="string_catalog_items",
    )
    op.drop_index(
        "ix_string_catalog_items_model_name", table_name="string_catalog_items"
    )
    op.drop_index("ix_string_catalog_items_brand", table_name="string_catalog_items")
    op.drop_table("string_catalog_items")
    op.drop_index("ix_profiles_user_id", table_name="profiles")
    op.drop_table("profiles")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_table("users")
