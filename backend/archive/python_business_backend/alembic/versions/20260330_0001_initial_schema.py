"""initial schema

Revision ID: 20260330_0001
Revises:
Create Date: 2026-03-30 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260330_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("app_users"):
        return

    op.create_table(
        "app_users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("auth_user_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
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
    op.create_index(
        "ix_app_users_auth_user_id", "app_users", ["auth_user_id"], unique=True
    )
    op.create_index("ix_app_users_email", "app_users", ["email"], unique=True)
    op.create_index(
        "ix_app_users_phone_number", "app_users", ["phone_number"], unique=True
    )

    op.create_table(
        "customer_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("skill_level", sa.String(length=50), nullable=True),
        sa.Column("playing_style", sa.String(length=50), nullable=True),
        sa.Column("play_frequency", sa.String(length=50), nullable=True),
        sa.Column("budget_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("preferred_tension", sa.Numeric(4, 1), nullable=True),
        sa.Column("durability_priority", sa.Integer(), nullable=True),
        sa.Column("repulsion_priority", sa.Integer(), nullable=True),
        sa.Column("control_priority", sa.Integer(), nullable=True),
        sa.Column("preferred_feel", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_customer_profiles_user_id", "customer_profiles", ["user_id"], unique=True
    )

    op.create_table(
        "strings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("external_id", sa.String(length=50), nullable=True),
        sa.Column("source_item_id", sa.Integer(), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=False),
        sa.Column("brand_en", sa.String(length=100), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("series", sa.String(length=50), nullable=True),
        sa.Column("series_en", sa.String(length=50), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("gauge_raw", sa.String(length=20), nullable=True),
        sa.Column("gauge_mm", sa.Numeric(4, 2), nullable=True),
        sa.Column("material", sa.String(length=100), nullable=True),
        sa.Column("material_en", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=100), nullable=True),
        sa.Column("rating", sa.Numeric(4, 2), nullable=True),
        sa.Column("rating_5_scale", sa.Numeric(4, 2), nullable=True),
        sa.Column("want_count", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("popularity_signal", sa.Integer(), nullable=True),
        sa.Column("feature_text", sa.Text(), nullable=True),
        sa.Column("feature_text_en", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("repulsion_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("durability_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("control_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("sound_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("tension_retention_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("value_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("availability_status", sa.String(length=20), nullable=False),
        sa.Column("recommended_tension_min", sa.Integer(), nullable=True),
        sa.Column("recommended_tension_max", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_strings_brand", "strings", ["brand"], unique=False)
    op.create_index("ix_strings_external_id", "strings", ["external_id"], unique=True)
    op.create_index("ix_strings_model_name", "strings", ["model_name"], unique=False)

    op.create_table(
        "string_tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("string_id", sa.String(length=36), nullable=False),
        sa.Column("tag_name", sa.String(length=100), nullable=False),
        sa.Column("tag_name_en", sa.String(length=100), nullable=True),
        sa.Column("votes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["string_id"], ["strings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_string_tags_string_id", "string_tags", ["string_id"], unique=False
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("customer_user_id", sa.String(length=36), nullable=False),
        sa.Column("string_id", sa.String(length=36), nullable=False),
        sa.Column("racket_brand", sa.String(length=100), nullable=True),
        sa.Column("racket_model", sa.String(length=100), nullable=True),
        sa.Column("requested_tension", sa.Numeric(4, 1), nullable=True),
        sa.Column("appointment_date", sa.Date(), nullable=True),
        sa.Column("appointment_slot", sa.String(length=30), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["customer_user_id"], ["app_users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["string_id"], ["strings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bookings_customer_user_id", "bookings", ["customer_user_id"], unique=False
    )
    op.create_index("ix_bookings_status", "bookings", ["status"], unique=False)
    op.create_index("ix_bookings_string_id", "bookings", ["string_id"], unique=False)

    op.create_table(
        "booking_status_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("booking_id", sa.String(length=36), nullable=False),
        sa.Column("old_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=False),
        sa.Column("changed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["app_users.id"]),
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
        sa.Column("customer_user_id", sa.String(length=36), nullable=False),
        sa.Column("input_snapshot", sa.Text(), nullable=False),
        sa.Column("result_snapshot", sa.Text(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_user_id"], ["app_users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_logs_customer_user_id",
        "recommendation_logs",
        ["customer_user_id"],
        unique=False,
    )

    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_password_reset_codes_phone_number",
        "password_reset_codes",
        ["phone_number"],
        unique=False,
    )
    op.create_index(
        "ix_password_reset_codes_user_id",
        "password_reset_codes",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_codes_user_id", table_name="password_reset_codes")
    op.drop_index(
        "ix_password_reset_codes_phone_number", table_name="password_reset_codes"
    )
    op.drop_table("password_reset_codes")
    op.drop_index(
        "ix_recommendation_logs_customer_user_id", table_name="recommendation_logs"
    )
    op.drop_table("recommendation_logs")
    op.drop_index(
        "ix_booking_status_history_booking_id", table_name="booking_status_history"
    )
    op.drop_table("booking_status_history")
    op.drop_index("ix_bookings_string_id", table_name="bookings")
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_customer_user_id", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_string_tags_string_id", table_name="string_tags")
    op.drop_table("string_tags")
    op.drop_index("ix_strings_model_name", table_name="strings")
    op.drop_index("ix_strings_external_id", table_name="strings")
    op.drop_index("ix_strings_brand", table_name="strings")
    op.drop_table("strings")
    op.drop_index("ix_customer_profiles_user_id", table_name="customer_profiles")
    op.drop_table("customer_profiles")
    op.drop_index("ix_app_users_phone_number", table_name="app_users")
    op.drop_index("ix_app_users_email", table_name="app_users")
    op.drop_index("ix_app_users_auth_user_id", table_name="app_users")
    op.drop_table("app_users")
