"""remove unused runtime compatibility and inactive catalog data

Revision ID: 20260902_0042
Revises: 20260902_0041
Create Date: 2026-09-02 00:00:00

The current runtime keeps recommendation runs as the only recommendation audit,
OpenWA as the only optional remote notification provider, and current payment
methods only. Inactive strings and their dependent historical bookings are
intentionally removed.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260902_0042"
down_revision = "20260902_0041"
branch_labels = None
depends_on = None


def _bind():
    return op.get_bind()


def _tables() -> set[str]:
    return set(sa.inspect(_bind()).get_table_names())


def _drop_column(table_name: str, column_name: str) -> None:
    columns = {column["name"] for column in sa.inspect(_bind()).get_columns(table_name)}
    if column_name not in columns:
        return
    if _bind().dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column(column_name)
        return
    for foreign_key in sa.inspect(_bind()).get_foreign_keys(table_name):
        if foreign_key.get("constrained_columns") == [column_name]:
            op.drop_constraint(
                foreign_key["name"],
                table_name,
                type_="foreignkey",
            )
    op.drop_column(table_name, column_name)


def _delete_inactive_catalog_data() -> None:
    bind = _bind()
    bind.execute(
        sa.text(
            """
            DELETE FROM bookings
            WHERE string_id IN (
                SELECT catalog_id FROM strings WHERE is_active IS FALSE
            )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM recommendation_run_items
            WHERE catalog_id IN (
                SELECT catalog_id FROM strings WHERE is_active IS FALSE
            )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM recommendation_runs
            WHERE NOT EXISTS (
                SELECT 1
                FROM recommendation_run_items
                WHERE recommendation_run_items.run_id = recommendation_runs.id
            )
            """
        )
    )
    bind.execute(sa.text("DELETE FROM strings WHERE is_active IS FALSE"))


def _restrict_payment_methods() -> None:
    bind = _bind()
    bind.execute(
        sa.text(
            "DELETE FROM payments WHERE method IN "
            "('card', 'online_banking', 'e_wallet')"
        )
    )
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("payments") as batch_op:
            batch_op.create_check_constraint(
                "ck_payments_current_method",
                "method IN ('qr_transfer', 'cash', 'wallet_balance')",
            )
    else:
        op.create_check_constraint(
            "ck_payments_current_method",
            "payments",
            "method IN ('qr_transfer', 'cash', 'wallet_balance')",
        )


def upgrade() -> None:
    tables = _tables()
    required = {
        "booking_status_history",
        "bookings",
        "notifications",
        "payments",
        "recommendation_run_items",
        "recommendation_runs",
        "strings",
    }
    missing = sorted(required - tables)
    if missing:
        raise RuntimeError(
            "Refusing cleanup because active tables are missing: " + ", ".join(missing)
        )

    _delete_inactive_catalog_data()
    _restrict_payment_methods()
    _drop_column("booking_status_history", "old_status")
    _drop_column("notifications", "device_token_id")

    for table_name in (
        "account_deletion_requests",
        "device_tokens",
        "recommendation_logs",
    ):
        if table_name in _tables():
            op.drop_table(table_name)

    inactive_count = (
        _bind()
        .execute(sa.text("SELECT COUNT(*) FROM strings WHERE is_active IS FALSE"))
        .scalar_one()
    )
    old_payment_count = (
        _bind()
        .execute(
            sa.text(
                "SELECT COUNT(*) FROM payments WHERE method IN "
                "('card', 'online_banking', 'e_wallet')"
            )
        )
        .scalar_one()
    )
    if inactive_count or old_payment_count:
        raise RuntimeError("Runtime compatibility cleanup did not complete")


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported because removed runtime data "
        "cannot be reconstructed safely."
    )
