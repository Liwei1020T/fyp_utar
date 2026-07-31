"""enforce authentication and one-active-token invariants

Revision ID: 20260731_0026
Revises: 20260726_0025
Create Date: 2026-07-31 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260731_0026"
down_revision = "20260726_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    user_columns = {item["name"] for item in inspector.get_columns("users")}
    if "auth_version" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "auth_version",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )

    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY phone_number
                        ORDER BY created_at DESC, id DESC
                    ) AS row_number
                FROM password_reset_codes
                WHERE used_at IS NULL
            )
            UPDATE password_reset_codes
            SET used_at = CURRENT_TIMESTAMP
            WHERE id IN (
                SELECT id FROM ranked WHERE row_number > 1
            )
            """
        )
    )
    reset_indexes = {
        item["name"] for item in inspector.get_indexes("password_reset_codes")
    }
    if "uq_password_reset_codes_one_active_phone" not in reset_indexes:
        op.create_index(
            "uq_password_reset_codes_one_active_phone",
            "password_reset_codes",
            ["phone_number"],
            unique=True,
            postgresql_where=sa.text("used_at IS NULL"),
            sqlite_where=sa.text("used_at IS NULL"),
        )

    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY booking_id
                        ORDER BY created_at DESC, id DESC
                    ) AS row_number
                FROM check_in_tokens
                WHERE used_at IS NULL AND revoked_at IS NULL
            )
            UPDATE check_in_tokens
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE id IN (
                SELECT id FROM ranked WHERE row_number > 1
            )
            """
        )
    )
    check_in_indexes = {
        item["name"] for item in inspector.get_indexes("check_in_tokens")
    }
    if "uq_check_in_tokens_one_active_booking" not in check_in_indexes:
        op.create_index(
            "uq_check_in_tokens_one_active_booking",
            "check_in_tokens",
            ["booking_id"],
            unique=True,
            postgresql_where=sa.text("used_at IS NULL AND revoked_at IS NULL"),
            sqlite_where=sa.text("used_at IS NULL AND revoked_at IS NULL"),
        )


def downgrade() -> None:
    op.drop_index(
        "uq_check_in_tokens_one_active_booking",
        table_name="check_in_tokens",
    )
    op.drop_index(
        "uq_password_reset_codes_one_active_phone",
        table_name="password_reset_codes",
    )
    op.drop_column("users", "auth_version")
