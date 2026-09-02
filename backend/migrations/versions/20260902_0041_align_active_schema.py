"""align the active ORM schema without changing business rows

Revision ID: 20260902_0041
Revises: 20260902_0040
Create Date: 2026-09-02 00:00:00

The active PostgreSQL schema predates several ORM constraint, index, length,
and numeric-precision declarations. This migration reconciles those definitions
after validating that all existing values fit. It does not delete rows.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260902_0041"
down_revision = "20260902_0040"
branch_labels = None
depends_on = None


def _bind():
    return op.get_bind()


def _inspector():
    return sa.inspect(_bind())


def _has_index(table_name: str, index_name: str) -> bool:
    return any(
        index["name"] == index_name for index in _inspector().get_indexes(table_name)
    )


def _has_unique_constraint(table_name: str, constraint_name: str) -> bool:
    return constraint_name in {
        constraint["name"]
        for constraint in _inspector().get_unique_constraints(table_name)
    }


def _has_brand_foreign_key() -> bool:
    return any(
        foreign_key.get("referred_table") == "brands"
        and foreign_key.get("constrained_columns") == ["brand_code"]
        for foreign_key in _inspector().get_foreign_keys("strings")
    )


def _max_length(table_name: str, column_name: str) -> int:
    value = (
        _bind()
        .execute(
            sa.text(f"SELECT COALESCE(MAX(length({column_name})), 0) FROM {table_name}")
        )
        .scalar_one()
    )
    return int(value)


def _assert_max_length(table_name: str, column_name: str, limit: int) -> None:
    actual = _max_length(table_name, column_name)
    if actual > limit:
        raise RuntimeError(
            f"Refusing schema alignment; {table_name}.{column_name} has "
            f"length {actual}, above the new limit {limit}"
        )


def _assert_max_abs(
    table_name: str, column_names: tuple[str, ...], limit: float
) -> None:
    expressions = ", ".join(f"MAX(ABS({column_name}))" for column_name in column_names)
    values = _bind().execute(sa.text(f"SELECT {expressions} FROM {table_name}")).one()
    actual = max((float(value) for value in values if value is not None), default=0.0)
    if actual > limit:
        raise RuntimeError(
            f"Refusing schema alignment; {table_name} contains a value above {limit}"
        )


def _assert_no_nulls(table_name: str, column_names: tuple[str, ...]) -> None:
    conditions = " OR ".join(f"{column_name} IS NULL" for column_name in column_names)
    null_count = (
        _bind()
        .execute(sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE {conditions}"))
        .scalar_one()
    )
    if null_count:
        raise RuntimeError(
            f"Refusing schema alignment; {table_name} has {null_count} rows with "
            "required values missing"
        )


def _assert_no_duplicate_strings() -> None:
    duplicate_count = (
        _bind()
        .execute(
            sa.text(
                """
            SELECT COUNT(*)
            FROM (
                SELECT display_name
                FROM strings
                GROUP BY display_name
                HAVING COUNT(*) > 1
            ) duplicates
            """
            )
        )
        .scalar_one()
    )
    if duplicate_count:
        raise RuntimeError(
            "Refusing schema alignment; strings.display_name contains duplicates"
        )


def _assert_string_brands_exist() -> None:
    orphan_count = (
        _bind()
        .execute(
            sa.text(
                """
            SELECT COUNT(*)
            FROM strings AS string_item
            LEFT JOIN brands ON brands.brand_code = string_item.brand_code
            WHERE brands.brand_code IS NULL
            """
            )
        )
        .scalar_one()
    )
    if orphan_count:
        raise RuntimeError(
            f"Refusing schema alignment; {orphan_count} strings have no matching brand"
        )


def _alter_columns(table_name: str, changes: tuple[dict[str, object], ...]) -> None:
    if not changes:
        return
    if _bind().dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch_op:
            for change in changes:
                batch_op.alter_column(**change)
        return
    for change in changes:
        op.alter_column(table_name, **change)


def _drop_unique_constraint(table_name: str, constraint_name: str) -> None:
    if not _has_unique_constraint(table_name, constraint_name):
        return
    if _bind().dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(constraint_name, type_="unique")
    else:
        op.drop_constraint(constraint_name, table_name, type_="unique")


def _replace_index(
    table_name: str,
    index_name: str,
    columns: list[str],
    *,
    unique: bool,
) -> None:
    if _has_index(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)
    op.create_index(index_name, table_name, columns, unique=unique)


def _ensure_index(
    table_name: str,
    index_name: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _ensure_strings_brand_foreign_key() -> None:
    if _has_brand_foreign_key():
        return
    if _bind().dialect.name == "sqlite":
        with op.batch_alter_table("strings") as batch_op:
            batch_op.create_foreign_key(
                "fk_strings_brand_code_brands",
                "brands",
                ["brand_code"],
                ["brand_code"],
            )
    else:
        op.create_foreign_key(
            "fk_strings_brand_code_brands",
            "strings",
            "brands",
            ["brand_code"],
            ["brand_code"],
        )


def upgrade() -> None:
    _assert_max_length("brands", "brand_code", 40)
    _assert_max_length("strings", "brand_code", 40)
    _assert_max_length("recommendation_feature_definitions", "data_type", 32)
    _assert_max_length("string_official_performance", "source_type", 40)
    _assert_max_abs(
        "recommendation_score_cache",
        (
            "content_score",
            "collaborative_score",
            "rule_score",
            "nlp_score",
            "final_score",
        ),
        99.9999,
    )
    _assert_max_abs("string_recommendation_matrix", ("normalized_score",), 99.9999)
    _assert_max_abs("user_preference_matrix", ("preference_weight",), 99.9999)
    _assert_no_nulls(
        "recommendation_score_cache",
        ("final_score", "rank_position", "rationale"),
    )
    _assert_no_duplicate_strings()
    _assert_string_brands_exist()

    _alter_columns(
        "brands",
        (
            {
                "column_name": "brand_code",
                "existing_type": sa.String(length=60),
                "type_": sa.String(length=40),
            },
        ),
    )
    _alter_columns(
        "recommendation_feature_definitions",
        (
            {
                "column_name": "feature_group",
                "existing_type": sa.String(length=60),
                "type_": sa.String(length=80),
            },
            {
                "column_name": "data_type",
                "existing_type": sa.String(length=40),
                "type_": sa.String(length=32),
            },
        ),
    )
    _alter_columns(
        "recommendation_score_cache",
        (
            {
                "column_name": "content_score",
                "existing_type": sa.Numeric(precision=8, scale=4),
                "type_": sa.Numeric(precision=6, scale=4),
            },
            {
                "column_name": "collaborative_score",
                "existing_type": sa.Numeric(precision=8, scale=4),
                "type_": sa.Numeric(precision=6, scale=4),
            },
            {
                "column_name": "rule_score",
                "existing_type": sa.Numeric(precision=8, scale=4),
                "type_": sa.Numeric(precision=6, scale=4),
            },
            {
                "column_name": "nlp_score",
                "existing_type": sa.Numeric(precision=8, scale=4),
                "type_": sa.Numeric(precision=6, scale=4),
            },
            {
                "column_name": "final_score",
                "existing_type": sa.Numeric(precision=8, scale=4),
                "type_": sa.Numeric(precision=6, scale=4),
                "nullable": False,
            },
            {
                "column_name": "rank_position",
                "existing_type": sa.Integer(),
                "nullable": False,
            },
            {
                "column_name": "rationale",
                "existing_type": sa.JSON(),
                "nullable": False,
            },
        ),
    )
    _alter_columns(
        "string_official_performance",
        (
            {
                "column_name": "source_type",
                "existing_type": sa.String(length=60),
                "type_": sa.String(length=40),
            },
            {
                "column_name": "source_name",
                "existing_type": sa.String(length=120),
                "type_": sa.String(length=160),
            },
        ),
    )
    _alter_columns(
        "string_recommendation_matrix",
        (
            {
                "column_name": "normalized_score",
                "existing_type": sa.Numeric(precision=8, scale=4),
                "type_": sa.Numeric(precision=6, scale=4),
            },
        ),
    )
    _alter_columns(
        "strings",
        (
            {
                "column_name": "brand_code",
                "existing_type": sa.String(length=60),
                "type_": sa.String(length=40),
            },
            {
                "column_name": "gauge_main_mm",
                "existing_type": sa.Float(),
                "type_": sa.Numeric(precision=4, scale=2),
            },
            {
                "column_name": "gauge_cross_mm",
                "existing_type": sa.Float(),
                "type_": sa.Numeric(precision=4, scale=2),
            },
            {
                "column_name": "source_language",
                "existing_type": sa.String(length=20),
                "type_": sa.String(length=32),
            },
            {
                "column_name": "original_series",
                "existing_type": sa.String(length=120),
                "type_": sa.String(length=160),
            },
        ),
    )
    _alter_columns(
        "user_preference_matrix",
        (
            {
                "column_name": "preference_weight",
                "existing_type": sa.Numeric(precision=8, scale=4),
                "type_": sa.Numeric(precision=6, scale=4),
            },
        ),
    )

    _drop_unique_constraint("check_in_tokens", "check_in_tokens_token_hash_key")
    _replace_index(
        "check_in_tokens",
        "ix_check_in_tokens_token_hash",
        ["token_hash"],
        unique=True,
    )
    _drop_unique_constraint("device_tokens", "device_tokens_token_key")
    _replace_index("device_tokens", "ix_device_tokens_token", ["token"], unique=True)
    _drop_unique_constraint("profiles", "profiles_user_id_key")
    _drop_unique_constraint(
        "racket_model_catalog",
        "racket_model_catalog_model_key_key",
    )
    _drop_unique_constraint("users", "users_phone_number_key")

    _replace_index("strings", "ix_strings_display_name", ["display_name"], unique=True)
    _ensure_index(
        "recommendation_feature_definitions",
        "ix_recommendation_feature_definitions_feature_group",
        ["feature_group"],
    )
    _ensure_index(
        "recommendation_feature_definitions",
        "ix_recommendation_feature_definitions_is_active",
        ["is_active"],
    )
    _ensure_index(
        "recommendation_score_cache",
        "ix_recommendation_score_cache_generated_at",
        ["generated_at"],
    )
    _ensure_index(
        "string_official_performance",
        "ix_string_official_performance_status",
        ["status"],
    )
    _ensure_index(
        "string_recommendation_matrix",
        "ix_string_recommendation_matrix_normalized_score",
        ["normalized_score"],
    )
    _ensure_index("strings", "ix_strings_is_active", ["is_active"])
    _ensure_index(
        "strings",
        "ix_strings_official_performance_status",
        ["official_performance_status"],
    )
    _ensure_strings_brand_foreign_key()


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported because schema alignment is "
        "the canonical active database shape."
    )
