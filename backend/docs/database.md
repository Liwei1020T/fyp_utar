# Database Ownership and Schema Strategy

## Source of Truth

SQLAlchemy models in [app/adapters/persistence/sqlalchemy/models](../app/adapters/persistence/sqlalchemy/models) plus Alembic revisions in [migrations](../migrations) are now the active schema source of truth for the backend.

The active migration sequence is:

- [20260404_0001_unified_python_backend.py](../migrations/versions/20260404_0001_unified_python_backend.py)
- [20260404_0002_password_reset_codes.py](../migrations/versions/20260404_0002_password_reset_codes.py)
- [20260404_0003_admin_booking_baseline.py](../migrations/versions/20260404_0003_admin_booking_baseline.py)
- [20260405_0004_inventory_fields.py](../migrations/versions/20260405_0004_inventory_fields.py)
- [20260405_0005_store_ops_tables.py](../migrations/versions/20260405_0005_store_ops_tables.py)
- [20260407_0006_booking_updates.py](../migrations/versions/20260407_0006_booking_updates.py)
- [20260411_0007_booking_update_photo_type.py](../migrations/versions/20260411_0007_booking_update_photo_type.py)
- [20260412_0008_normalize_string_catalog.py](../migrations/versions/20260412_0008_normalize_string_catalog.py)
- [20260412_0009_fix_official_performance_numeric_types.py](../migrations/versions/20260412_0009_fix_official_performance_numeric_types.py)
- [20260412_0010_activate_recommendation_cache_breakdown.py](../migrations/versions/20260412_0010_activate_recommendation_cache_breakdown.py)
- [20260412_0011_preference_raw_score_and_features.py](../migrations/versions/20260412_0011_preference_raw_score_and_features.py)
- [20260413_0012_admin_string_editor_fields.py](../migrations/versions/20260413_0012_admin_string_editor_fields.py)
- [20260413_0013_store_settings_trending_strings.py](../migrations/versions/20260413_0013_store_settings_trending_strings.py)
- [20260413_0014_schema_drift_cleanup.py](../migrations/versions/20260413_0014_schema_drift_cleanup.py)

## Active Business Tables

### `users`

- phone-first identity
- `phone_number` is unique
- `username` is business-visible profile text
- `auth_provider` and `external_auth_id` keep Firebase-ready seams without making Firebase mandatory

### `profiles`

Stores the canonical recommendation and profile fields:

- `skill_level`
- `playing_style`
- `budget_min`
- `budget_max`
- `preferred_tension`
- `game_type`
- `frequency_per_week`
- `pref_attack`
- `pref_comfort`
- `pref_control`
- `pref_durability`
- `pref_elasticity`
- `pref_sound`
- `pref_string_movement`
- `pref_tension_retention`
- `pref_value_for_money`

### Catalog Normalization

The old `string_catalog_items` table was split into a normalized catalog subsystem:

- `brands`
  - normalized brand master data
- `strings`
  - long-term master catalog rows in English
  - one row per string model
  - stores names, descriptions, gauge data, materials, colors, source traceability, and active status
- `string_catalog_metrics`
  - community counts and rating separated from master product truth
- `string_catalog_tags`
  - multi-tag community signals per string
- `string_official_performance`
  - official/manual performance values only
  - intentionally separate from NLP or rule-derived scores
- `inventory_items`
  - current single-store stock, reorder settings, and pricing
- `inventory_movements`
  - append-only inventory adjustment history
- `recommendation_feature_definitions`
  - recommendation feature metadata
- `string_recommendation_matrix`
  - item-side feature matrix with explicit source layers
- `user_preference_matrix`
  - user-side preference vectors
- `recommendation_score_cache`
  - cached recommendation results per user and algorithm version, including the active score breakdown and rationale payload

The migration keeps the legacy flat table only as historical migrated state during transition. Alembic autogenerate intentionally ignores `string_catalog_items_legacy`, and the active runtime schema now reads catalog and inventory data from the normalized tables above.

### `strings`

Stores the master string catalog only:

- `catalog_id`
- `brand_code`
- `display_name`
- `model_name`
- `series_key` / `series_label`
- `is_hybrid`
- `gauge_main_mm` / `gauge_cross_mm` / `gauge_label`
- `material_summary_en`
- `color_options_en`
- `short_description`
- `full_description`
- `official_performance_status`
- `source_dataset_url`
- `source_language`
- `original_*` traceability fields
- `is_active`

Important rule:
- recommendation-derived aspect scores do not live here
- official/manual scores do not live here
- inventory state does not live here

### `string_official_performance`

Stores only official or manually curated performance values. Missing values stay null and rows default to `pending_manual_fill`.

### `inventory_items`

Stores the current store-facing inventory and pricing state:

- `current_stock`
- `reserved_stock`
- `available_stock`
- `reorder_level`
- `reorder_quantity`
- `cost_price`
- `selling_price`
- `pricing_mode`
- `availability_status`
- `is_active`

### `string_recommendation_matrix`

Stores item-side recommendation features with explicit provenance via `source_layer`.
Current seed/import behavior keeps two important layers separate:

- `hybrid_derived`
  - compatibility fallback rows backfilled from the old flat catalog heuristics
- `nlp_review`
  - the primary item-side recommendation matrix imported from `../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`

Important rules:

- `nlp_review` rows are derived recommendation inputs, not master catalog truth
- official/manual values stay in `string_official_performance`
- recommendation matrix values do not get copied into `strings`
- re-imports are idempotent on `(catalog_id, feature_key, source_layer)`
- both CSV and XLSX practical matrix sources are supported; V9 XLSX is the current default runtime source
- before import, the backend sanitizes the source file to a runtime whitelist so only the currently used live-scoring fields and matching metadata are written into the feature store; stale `nlp_review` rows outside that whitelist are pruned on re-import

Current `nlp_review` runtime import keys are:

- `repulsion` (mapped from source column `attack`)
- `comfort`
- `control`
- `durability`
- `elasticity`
- `sound`
- `string_movement`
- `tension_retention`

Support keys such as `value_for_money`, `stability_score`, `all_round_score`, `attacking_fit_score`, `control_fit_score`, and `beginner_fit_score` may still appear from older compatibility rows (for example `hybrid_derived`) but are not imported by the current `nlp_review` whitelist.

### `user_preference_matrix`

Stores the user-side recommendation vector derived from profile/onboarding data. The active profile-derived rows use `source_layer='profile'`.

Current persisted feature rows use canonical scoring keys from `recommendation_feature_definitions`.
Raw 1-to-10 UI inputs are stored in `raw_score`, and backend-normalized weights are stored in `preference_weight`.

Current persisted feature rows include:

- core preference weights: `repulsion`, `control`, `durability`, `comfort`, `sound`, `elasticity`, `tension_retention`, and `string_movement`

These rows are regenerated when a complete profile is saved and when profile recommendations are generated.

### `recommendation_score_cache`

Stores the latest generated recommendation rows per `(user_id, catalog_id, algorithm_version)`.

The active algorithm version is `fyp1_preference_official_nlp_rule_budget_v3`.

Score fields:

- `preference_match_score`
- `rule_fit_score`
- `budget_fit_score`
- `nlp_review_score`
- `final_score`

Compatibility columns (`content_score`, `collaborative_score`, `rule_score`, and `nlp_score`) remain available for older inspection/debug paths. FYP1 does not write collaborative-filtering scores; `collaborative_score` should stay `NULL`. The `rationale` JSON stores raw user scores, normalized weights, effective official+NLP feature scores, NLP review evidence, rule events, profile context, and top human-readable reasons.

### `store_business_hours`

Stores the single-store weekly schedule plus special closed dates used to generate booking slot availability.

### `store_settings`

Stores the single-store support copy, policy text, contact details, and other admin-facing settings used by the operations UI.

### `bookings`

Stores service-tracking bookings only. Slot conflict detection remains intentionally out of scope.
Current lifecycle values are `awaiting_dropoff`, `in_progress`, `ready_for_collection`, `completed`, `cancelled`, and `rejected`.

### `booking_status_history`

Stores booking status transitions plus optional admin operator notes for auditability.

### `booking_updates`

Stores player/admin booking comments and optional uploaded photo metadata. Photo files are stored locally under `backend/var/uploads/booking-updates/` for the FYP demo and exposed through relative `/media/...` URLs.

### `recommendation_logs`

Stores request snapshots, result snapshots, and `algorithm_version`.

The active runtime schema authority is limited to `app/adapters/persistence/sqlalchemy/models/` plus the root `migrations/` history.
