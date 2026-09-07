"""remove deferred external-auth storage

Revision ID: 20260907_0047
Revises: 20260907_0046
Create Date: 2026-09-07 00:00:00

Firebase authentication is not implemented. The domain and API response keep
the old compatibility fields as a local/None projection, while the unused
database storage is removed. Fail closed if another database contains an
external provider or external authentication ID.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260907_0047"
down_revision = "20260907_0046"
branch_labels = None
depends_on = None


def _columns() -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}


def _assert_no_external_values(columns: set[str]) -> None:
    bind = op.get_bind()
    if "auth_provider" in columns:
        non_local_count = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM users "
                "WHERE auth_provider IS NULL OR auth_provider <> 'local'"
            )
        ).scalar_one()
        if non_local_count:
            raise RuntimeError(
                "Refusing to remove deferred auth storage: "
                f"{non_local_count} user rows use a non-local provider"
            )
    if "external_auth_id" in columns:
        external_id_count = bind.execute(
            sa.text("SELECT COUNT(*) FROM users WHERE external_auth_id IS NOT NULL")
        ).scalar_one()
        if external_id_count:
            raise RuntimeError(
                "Refusing to remove deferred auth storage: "
                f"{external_id_count} user rows contain an external auth ID"
            )


def upgrade() -> None:
    columns = _columns()
    auth_columns = {"auth_provider", "external_auth_id"} & columns
    if not auth_columns:
        return
    _assert_no_external_values(columns)

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch_op:
            if "external_auth_id" in columns:
                batch_op.drop_column("external_auth_id")
            if "auth_provider" in columns:
                batch_op.drop_column("auth_provider")
        return
    if "external_auth_id" in columns:
        op.drop_column("users", "external_auth_id")
    if "auth_provider" in columns:
        op.drop_column("users", "auth_provider")


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns()
    unique_constraints = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("users")
    }
    auth_provider = sa.Column(
        "auth_provider",
        sa.String(40),
        nullable=False,
        server_default="local",
    )
    external_auth_id = sa.Column("external_auth_id", sa.String(64), nullable=True)

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch_op:
            if "auth_provider" not in columns:
                batch_op.add_column(auth_provider)
            if "external_auth_id" not in columns:
                batch_op.add_column(external_auth_id)
            if "users_external_auth_id_key" not in unique_constraints:
                batch_op.create_unique_constraint(
                    "users_external_auth_id_key",
                    ["external_auth_id"],
                )
        return
    if "auth_provider" not in columns:
        op.add_column("users", auth_provider)
    if "external_auth_id" not in columns:
        op.add_column("users", external_auth_id)
    if "users_external_auth_id_key" not in unique_constraints:
        op.create_unique_constraint(
            "users_external_auth_id_key",
            "users",
            ["external_auth_id"],
        )
