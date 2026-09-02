"""converge persisted recommendation data on canonical keys

Revision ID: 20260902_0045
Revises: 20260902_0044
Create Date: 2026-09-02 00:00:00

The active recommendation runtime stores canonical feature keys. Older
normalized databases may still contain the three former support-key names, so
this migration moves those rows and definitions before the runtime stops
handling them. Pre-V14 score caches are also disposable and are removed because
the current cache payload uses the V14 rationale contract.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260902_0045"
down_revision = "20260902_0044"
branch_labels = None
depends_on = None

LEGACY_TO_CANONICAL = {
    "beginner_fit_score": "beginner_fit",
    "stability_score": "stability",
    "all_round_score": "all_round",
}
CURRENT_ALGORITHM_VERSION = "fyp1_weighted_preferences_feedback_racket_cf_personal_v14"


def _bind():
    return op.get_bind()


def _ensure_canonical_definitions(bind) -> None:
    for legacy_key, canonical_key in LEGACY_TO_CANONICAL.items():
        bind.execute(
            sa.text(
                """
                INSERT INTO recommendation_feature_definitions (
                    feature_key, feature_label, feature_group, data_type,
                    min_value, max_value, description, is_active
                )
                SELECT
                    CAST(:canonical_key AS VARCHAR(80)), feature_label,
                    feature_group, data_type,
                    min_value, max_value, description, is_active
                FROM recommendation_feature_definitions
                WHERE feature_key = CAST(:legacy_key AS VARCHAR(80))
                  AND NOT EXISTS (
                      SELECT 1
                      FROM recommendation_feature_definitions
                      WHERE feature_key = CAST(:canonical_key AS VARCHAR(80))
                  )
                """
            ),
            {
                "legacy_key": legacy_key,
                "canonical_key": canonical_key,
            },
        )


def _converge_string_matrix(bind) -> None:
    legacy_keys = tuple(LEGACY_TO_CANONICAL)
    placeholders = ", ".join(f":key_{index}" for index in range(len(legacy_keys)))
    rows = (
        bind.execute(
            sa.text(
                f"""
            SELECT catalog_id, feature_key, source_layer,
                   raw_value, normalized_score, evidence_note
            FROM string_recommendation_matrix
            WHERE feature_key IN ({placeholders})
            """
            ),
            {f"key_{index}": key for index, key in enumerate(legacy_keys)},
        )
        .mappings()
        .all()
    )

    for row in rows:
        canonical_key = LEGACY_TO_CANONICAL[row["feature_key"]]
        replacement = (
            bind.execute(
                sa.text(
                    """
                SELECT raw_value, normalized_score, evidence_note
                FROM string_recommendation_matrix
                WHERE catalog_id = :catalog_id
                  AND feature_key = :canonical_key
                  AND source_layer = :source_layer
                """
                ),
                {
                    "catalog_id": row["catalog_id"],
                    "canonical_key": canonical_key,
                    "source_layer": row["source_layer"],
                },
            )
            .mappings()
            .first()
        )

        identifiers = {
            "catalog_id": row["catalog_id"],
            "legacy_key": row["feature_key"],
            "source_layer": row["source_layer"],
        }
        if replacement is None:
            bind.execute(
                sa.text(
                    """
                    UPDATE string_recommendation_matrix
                    SET feature_key = :canonical_key
                    WHERE catalog_id = :catalog_id
                      AND feature_key = :legacy_key
                      AND source_layer = :source_layer
                    """
                ),
                {**identifiers, "canonical_key": canonical_key},
            )
            continue

        if (
            replacement["normalized_score"] is None
            and row["normalized_score"] is not None
        ):
            bind.execute(
                sa.text(
                    """
                    UPDATE string_recommendation_matrix
                    SET raw_value = :raw_value,
                        normalized_score = :normalized_score,
                        evidence_note = :evidence_note
                    WHERE catalog_id = :catalog_id
                      AND feature_key = :canonical_key
                      AND source_layer = :source_layer
                    """
                ),
                {
                    **identifiers,
                    "canonical_key": canonical_key,
                    "raw_value": row["raw_value"],
                    "normalized_score": row["normalized_score"],
                    "evidence_note": row["evidence_note"],
                },
            )

        bind.execute(
            sa.text(
                """
                DELETE FROM string_recommendation_matrix
                WHERE catalog_id = :catalog_id
                  AND feature_key = :legacy_key
                  AND source_layer = :source_layer
                """
            ),
            identifiers,
        )


def _converge_user_preferences(bind) -> None:
    legacy_keys = tuple(LEGACY_TO_CANONICAL)
    placeholders = ", ".join(f":key_{index}" for index in range(len(legacy_keys)))
    rows = (
        bind.execute(
            sa.text(
                f"""
            SELECT user_id, feature_key, source_layer,
                   raw_score, preference_weight, preferred_min, preferred_max
            FROM user_preference_matrix
            WHERE feature_key IN ({placeholders})
            """
            ),
            {f"key_{index}": key for index, key in enumerate(legacy_keys)},
        )
        .mappings()
        .all()
    )

    for row in rows:
        canonical_key = LEGACY_TO_CANONICAL[row["feature_key"]]
        identifiers = {
            "user_id": row["user_id"],
            "legacy_key": row["feature_key"],
            "source_layer": row["source_layer"],
        }
        replacement = (
            bind.execute(
                sa.text(
                    """
                SELECT raw_score, preference_weight, preferred_min, preferred_max
                FROM user_preference_matrix
                WHERE user_id = :user_id
                  AND feature_key = :canonical_key
                  AND source_layer = :source_layer
                """
                ),
                {
                    "user_id": row["user_id"],
                    "canonical_key": canonical_key,
                    "source_layer": row["source_layer"],
                },
            )
            .mappings()
            .first()
        )

        if replacement is None:
            bind.execute(
                sa.text(
                    """
                    UPDATE user_preference_matrix
                    SET feature_key = :canonical_key
                    WHERE user_id = :user_id
                      AND feature_key = :legacy_key
                      AND source_layer = :source_layer
                    """
                ),
                {**identifiers, "canonical_key": canonical_key},
            )
            continue

        updates = {
            field: row[field]
            for field in (
                "raw_score",
                "preference_weight",
                "preferred_min",
                "preferred_max",
            )
            if replacement[field] is None and row[field] is not None
        }
        if updates:
            assignments = ", ".join(f"{field} = :{field}" for field in updates)
            bind.execute(
                sa.text(
                    f"""
                    UPDATE user_preference_matrix
                    SET {assignments}
                    WHERE user_id = :user_id
                      AND feature_key = :canonical_key
                      AND source_layer = :source_layer
                    """
                ),
                {
                    **identifiers,
                    "canonical_key": canonical_key,
                    **updates,
                },
            )

        bind.execute(
            sa.text(
                """
                DELETE FROM user_preference_matrix
                WHERE user_id = :user_id
                  AND feature_key = :legacy_key
                  AND source_layer = :source_layer
                """
            ),
            identifiers,
        )


def _remove_legacy_definitions(bind) -> None:
    for legacy_key in LEGACY_TO_CANONICAL:
        bind.execute(
            sa.text(
                "DELETE FROM recommendation_feature_definitions "
                "WHERE feature_key = :legacy_key"
            ),
            {"legacy_key": legacy_key},
        )


def _assert_canonical_keys(bind) -> None:
    legacy_keys = tuple(LEGACY_TO_CANONICAL)
    placeholders = ", ".join(f":key_{index}" for index in range(len(legacy_keys)))
    parameters = {f"key_{index}": key for index, key in enumerate(legacy_keys)}
    for table_name in (
        "recommendation_feature_definitions",
        "string_recommendation_matrix",
        "user_preference_matrix",
    ):
        remaining = bind.execute(
            sa.text(
                f"SELECT COUNT(*) FROM {table_name} "
                f"WHERE feature_key IN ({placeholders})"
            ),
            parameters,
        ).scalar_one()
        if remaining:
            raise RuntimeError(
                f"Canonical feature-key migration left {remaining} legacy rows "
                f"in {table_name}"
            )


def upgrade() -> None:
    bind = _bind()
    _ensure_canonical_definitions(bind)
    _converge_string_matrix(bind)
    _converge_user_preferences(bind)
    _remove_legacy_definitions(bind)
    bind.execute(
        sa.text(
            "DELETE FROM recommendation_score_cache "
            "WHERE algorithm_version != :current_algorithm_version"
        ),
        {"current_algorithm_version": CURRENT_ALGORITHM_VERSION},
    )
    _assert_canonical_keys(bind)


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported because canonical feature-key "
        "data and removed score caches cannot be reconstructed safely."
    )
