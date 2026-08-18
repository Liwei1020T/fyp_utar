"""add QR payment configuration and payment proof paths

Revision ID: 20260818_0032
Revises: 20260817_0031
Create Date: 2026-08-18 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260818_0032"
down_revision = "20260817_0031"
branch_labels = None
depends_on = None

QR_PAYMENT_PROOF_CHECK = "method <> 'qr_transfer' OR proof_path IS NOT NULL"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    store_columns = {item["name"] for item in inspector.get_columns("store_settings")}
    if "payment_qr_path" not in store_columns:
        op.add_column(
            "store_settings",
            sa.Column("payment_qr_path", sa.Text(), nullable=True),
        )

    payment_columns = {item["name"] for item in inspector.get_columns("payments")}
    if "proof_path" not in payment_columns:
        op.add_column("payments", sa.Column("proof_path", sa.Text(), nullable=True))

    checks = {item["name"] for item in inspector.get_check_constraints("payments")}
    if "ck_payments_qr_transfer_proof" not in checks:
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("payments") as batch_op:
                batch_op.create_check_constraint(
                    "ck_payments_qr_transfer_proof",
                    QR_PAYMENT_PROOF_CHECK,
                )
        else:
            op.create_check_constraint(
                "ck_payments_qr_transfer_proof",
                "payments",
                QR_PAYMENT_PROOF_CHECK,
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    checks = {item["name"] for item in inspector.get_check_constraints("payments")}
    if "ck_payments_qr_transfer_proof" in checks:
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("payments") as batch_op:
                batch_op.drop_constraint(
                    "ck_payments_qr_transfer_proof",
                    type_="check",
                )
        else:
            op.drop_constraint(
                "ck_payments_qr_transfer_proof",
                "payments",
                type_="check",
            )

    payment_columns = {item["name"] for item in inspector.get_columns("payments")}
    if "proof_path" in payment_columns:
        op.drop_column("payments", "proof_path")

    store_columns = {item["name"] for item in inspector.get_columns("store_settings")}
    if "payment_qr_path" in store_columns:
        op.drop_column("store_settings", "payment_qr_path")
