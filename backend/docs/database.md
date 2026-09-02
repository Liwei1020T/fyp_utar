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
- [20260414_0015_fyp1_recommendation_alignment.py](../migrations/versions/20260414_0015_fyp1_recommendation_alignment.py)
- [20260414_0016_repair_recommendation_schema_drift.py](../migrations/versions/20260414_0016_repair_recommendation_schema_drift.py)
- [20260414_0017_remove_legacy_budget_range_columns.py](../migrations/versions/20260414_0017_remove_legacy_budget_range_columns.py)
- [20260423_0018_repair_booking_columns_drift.py](../migrations/versions/20260423_0018_repair_booking_columns_drift.py)
- [20260723_0019_notification_preferences.py](../migrations/versions/20260723_0019_notification_preferences.py)
- [20260723_0020_commerce_ledger.py](../migrations/versions/20260723_0020_commerce_ledger.py)
- [20260723_0021_notification_reads.py](../migrations/versions/20260723_0021_notification_reads.py)
- [20260723_0022_rackets_feedback.py](../migrations/versions/20260723_0022_rackets_feedback.py)
- [20260723_0023_booking_conversations.py](../migrations/versions/20260723_0023_booking_conversations.py)
- [20260723_0024_booking_update_channel.py](../migrations/versions/20260723_0024_booking_update_channel.py)
- [20260726_0025_player_admin_operations.py](../migrations/versions/20260726_0025_player_admin_operations.py)
- [20260731_0026_auth_and_token_invariants.py](../migrations/versions/20260731_0026_auth_and_token_invariants.py)
- [20260811_0027_recommendation_preferences.py](../migrations/versions/20260811_0027_recommendation_preferences.py)
- [20260812_0028_remove_recommendation_confidence_metadata.py](../migrations/versions/20260812_0028_remove_recommendation_confidence_metadata.py)
- [20260813_0029_feedback_provenance.py](../migrations/versions/20260813_0029_feedback_provenance.py)
- [20260817_0030_general_support_conversations.py](../migrations/versions/20260817_0030_general_support_conversations.py)
- [20260817_0031_clean_catalog_descriptions.py](../migrations/versions/20260817_0031_clean_catalog_descriptions.py)
- [20260818_0032_qr_payment_proofs.py](../migrations/versions/20260818_0032_qr_payment_proofs.py)
- [20260825_0033_remove_feedback_durability.py](../migrations/versions/20260825_0033_remove_feedback_durability.py)
- [20260825_0034_remove_unused_store_service_price.py](../migrations/versions/20260825_0034_remove_unused_store_service_price.py)
- [20260825_0035_remove_official_performance_source_url.py](../migrations/versions/20260825_0035_remove_official_performance_source_url.py)
- [20260826_0036_seed_official_performance.py](../migrations/versions/20260826_0036_seed_official_performance.py)
- [20260826_0037_seed_store_settings.py](../migrations/versions/20260826_0037_seed_store_settings.py)
- [20260831_0038_feedback_catalog_terminology.py](../migrations/versions/20260831_0038_feedback_catalog_terminology.py)
- [20260902_0039_racket_model_catalog.py](../migrations/versions/20260902_0039_racket_model_catalog.py)
- [20260902_0040_remove_legacy_feedback_and_catalog_tables.py](../migrations/versions/20260902_0040_remove_legacy_feedback_and_catalog_tables.py)
- [20260902_0041_align_active_schema.py](../migrations/versions/20260902_0041_align_active_schema.py)
- [20260902_0042_remove_unused_runtime_compatibility.py](../migrations/versions/20260902_0042_remove_unused_runtime_compatibility.py)
- [20260902_0043_remove_unused_recommendation_score_columns.py](../migrations/versions/20260902_0043_remove_unused_recommendation_score_columns.py)
- [20260902_0044_remove_legacy_preview_runs.py](../migrations/versions/20260902_0044_remove_legacy_preview_runs.py)

Revisions 0019–0025 can adopt complete pre-existing tables while still adding
missing columns to older databases. This keeps historical local databases
upgradeable without stamping over real schema gaps; arbitrary partially
created tables remain unsupported. New runtime schemas are created only by
Alembic.

At the current head (`20260902_0044`), the runtime contains the 32 application
tables represented by the SQLAlchemy models, plus Alembic's `alembic_version`
metadata table. Every application table has a current model and a live
repository, route, use case, seed, or audit consumer; removed legacy tables and
unused recommendation score columns are not part of the active schema.

Live verification on 2026-09-02 matched the ORM table set exactly: 33 public
tables total, with 12 strings and 12 inventory rows, no inactive or non-approved
catalog rows, no orphan recommendation rows, and no legacy preview markers.
`store_settings` and `store_business_hours` were both present.

## Active Business Tables

### `users`

- phone-first identity
- `phone_number` is unique
- `username` is business-visible profile text
- `auth_version` invalidates all previously issued JWTs after a password change
- `auth_provider` and `external_auth_id` keep Firebase-ready seams without making Firebase mandatory

### `password_reset_codes`

Stores hashed, expiring verification codes. A partial unique index permits only
one unused code per phone number; requesting a replacement locks the user row
and marks the prior code used before insertion.

### `profiles`

Stores the canonical recommendation and profile fields:

- `skill_level`
- `playing_style`
- `preferred_tension`
- `frequency_per_week`
- `preferred_feel`
- `preferred_gauge`
- `recent_goal`
- `pref_attack`
- `pref_comfort`
- `pref_control`
- `pref_durability`
- `pref_elasticity`
- `pref_sound`
- `pref_string_movement`
- `pref_tension_retention`
- `pref_value_for_money`
- `notification_preferences`
- `privacy_settings`

### Catalog Normalization

The old `string_catalog_items` table was split into a normalized catalog subsystem:

- `brands`
  - normalized brand master data
- `strings`
  - long-term master catalog rows in English
  - one row per string model
  - stores names, descriptions, gauge data, materials, colors, source traceability, and active status
- `string_catalog_metrics`
  - feedback counts and rating separated from master product truth
- `string_catalog_tags`
  - multi-tag feedback signals per string
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

The active runtime schema reads catalog and inventory data only from the normalized tables above. Migration `20260902_0040` removes leftover `string_catalog_items`, `string_catalog_items_legacy`, and `string_inventory_items` tables after checking that bookings still resolve through `strings`; these compatibility tables are not part of the active schema.

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

Stores official or manually curated performance values. The approved 12-string
cohort is seeded with complete `manual_reviewed` values. Non-approved source
records are not seeded into the runtime database.

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
  - active fallback rows derived for the approved cohort when a primary matrix
    value is unavailable; this is a row layer, not a legacy table
- `nlp_review`
  - the primary item-side recommendation matrix imported from `../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`

Important rules:

- `nlp_review` rows are derived recommendation inputs, not master catalog truth
- official/manual values stay in `string_official_performance`
- recommendation matrix values do not get copied into `strings`
- re-imports are idempotent on `(catalog_id, feature_key, source_layer)`
- both CSV and XLSX practical matrix sources are supported; the independent 12-by-9 MacBERT XLSX is the current default runtime source and V9 remains protected and separate
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

Support keys such as `value_for_money`, `stability_score`, `all_round_score`, `attacking_fit_score`, `control_fit_score`, and `beginner_fit_score` may appear in the active `hybrid_derived` fallback layer but are not imported by the current `nlp_review` whitelist.

### `user_preference_matrix`

Stores the user-side recommendation vector derived from profile/onboarding data. The active profile-derived rows use `source_layer='profile'`.

Current persisted feature rows use canonical scoring keys from `recommendation_feature_definitions`.
Raw 1-to-10 UI inputs are stored in `raw_score`, and backend-normalized weights are stored in `preference_weight`.

Current persisted feature rows include:

- core preference weights: `repulsion`, `control`, `durability`, `comfort`, `sound`, `elasticity`, `tension_retention`, `string_movement`, and `value_for_money`

These rows are regenerated when a complete profile is saved and when profile recommendations are generated.

### `recommendation_score_cache`

Stores the latest generated recommendation rows per `(user_id, catalog_id, algorithm_version)`.

The active algorithm version is
`fyp1_weighted_preferences_feedback_racket_cf_personal_v14`.

Profile saves invalidate that user's cache. Matrix content changes invalidate
all score-cache rows, while an unchanged startup import preserves them. Personal
history feedback invalidates that user's cache; cached reads also exclude
inactive or unavailable inventory.

Score fields:

- `preference_match_score`
- `rule_fit_score`
- `value_for_money_score`
- `nlp_review_score`
- `final_score`

The cache stores only the current explicit score fields. Racket-conditioned
collaborative evidence remains in the rationale audit payload and has a bounded
non-zero ranking weight only after the three-distinct-user exact-model gate
passes. The
`rationale` JSON stores preference inputs, effective scores, feedback snapshot
and source versions, racket context, CF shadow evidence, rule events, and reasons.

### `store_business_hours`

Stores the single-store weekly schedule plus special closed dates used to generate booking slot availability. A configured snapshot is kept in `data/store_settings_seed.json` for fresh database rebuilds.

### `store_settings`

Stores the single-store support copy, policy text, contact details, booking
notes, persisted `trending_string_ids` used as the player-facing Featured strings
selection, notification switches, and the optional server-owned `payment_qr_path` used for manual QR
transfers. The configured snapshot is seeded only when the row is missing.

### `bookings`

Stores service-tracking bookings. Creation uses a server-owned slot ID,
validates store schedule and future time, and reserves slot capacity under a
database lock.
Current lifecycle values are `awaiting_dropoff`, `in_progress`, `ready_for_collection`, `completed`, `cancelled`, and `rejected`.
An optional owned `racket_id` links a durable physical racket while
`racket_brand` and `racket_model` retain the booking-time snapshot.
`service_method` records counter drop-off or a requested pickup handover.

### `booking_status_history`

Stores booking status transitions plus optional admin operator notes for auditability.

### `booking_updates`

Stores player/admin booking comments and optional uploaded photo metadata. Photo
files are stored locally under `backend/var/uploads/booking-updates/` for the
FYP demo and exposed through time-limited signed `/api/media/...` URLs.
The `channel` field distinguishes ordinary service updates from persisted
booking-conversation messages.

### `booking_conversations`

Stores one support-conversation state record per booking, including the support
request time and player/admin read timestamps. Message bodies remain in
`booking_updates` so the booking keeps one chronological activity trail.

### `support_conversations` and `support_conversation_messages`

Store one reusable booking-free human-support thread per player. These rows are
separate from booking history, while sharing the same player/admin API and read
state behavior.

### `rackets`

Stores user-owned physical racket passports with a stable ID, nickname,
brand/model, optional frame metadata, preferred use, and notes.

### `racket_model_catalog`

Stores the admin-managed brand/model choices shown to players. The normalized
`model_key` is unique; deactivation hides a model from new selections while
preserving existing racket passports and booking snapshots.

### `booking_feedback`

Stores one structured feedback row per completed booking. The unique booking
constraint and ownership checks prevent duplicate or cross-user submissions.
Optional 1-to-5 detail fields store recommendation relevance, string and
tension satisfaction, comfort, control, and repulsion. The
`20260825_0033` migration removes the legacy feedback durability columns and
field-level confirmation metadata; catalogue and player-preference durability
remain separate recommendation data.

Migration `20260902_0040` removes the deprecated per-booking
`sentiment_tags` field. Current feedback keeps structured ratings, optional
comments, and the nullable `would_use_again` answer; existing unanswered rows
are not guessed or deleted.

The `20260825_0034` migration removes the unused store service-price column;
booking charges now come only from the selected string price.

The `20260825_0035` migration removes the unused official-performance source URL;
catalog and NLP provenance remain separate.

The `20260826_0036` migration seeds the manually reviewed official performance
values for the approved 12-string cohort from the canonical catalog source.

The `20260826_0037` migration seeds the configured single-store settings and
business-hours snapshot from `data/store_settings_seed.json`. It only inserts
missing rows, so later administrator edits are not overwritten during upgrades.

The `20260831_0038` migration renames the catalog metric column to
`feedback_rating`, rewrites derived matrix and description labels to
`feedback_signal`, and backfills missing feedback metrics/tags from the checked-in
catalog seed without overwriting existing values. The active runtime has no
compatibility column or route for the previous terminology; the old names remain
only inside immutable migration history so older databases can upgrade safely.

### `check_in_tokens`

Stores expiring one-time booking check-in digests. Raw QR values are never
persisted; used and revoked timestamps prevent replay. A partial unique index
permits only one unused, unrevoked token per booking.

### `notifications`

Stores each admin-composed in-app delivery and its latest optional OpenWA
attempt status.

### `notification_reads`

Stores stable derived notification event IDs that a user has read. Notification
content remains derived from owned source records rather than duplicated.

### `payments`

Stores booking-payment and wallet-top-up records:

- user and optional booking ownership
- method and status
- server-owned amount and unique reference
- `booking_payment` or `wallet_top_up` type
- optional immutable `proof_path` for new `qr_transfer` payments
- audit timestamps and shop verification note

New external records use `qr_transfer` or `cash` and remain `pending` until
admin verification. QR transfer requires an uploaded JPG/PNG/WEBP proof stored
under the payment-proofs upload area; cash keeps `proof_path` null. Wallet
booking payments may complete immediately after a server-side balance check.

### `wallet_transactions`

Append-only credit/debit ledger rows linked one-to-one to a completed payment.
Wallet balance is derived from this ledger; it is not a client-editable stored
counter.

### `recommendation_runs` and `recommendation_run_items`

Store immutable admin-audit history for generated recommendations:

- the run keeps request/profile snapshots plus algorithm, matrix, and feature
  source versions;
- item rows keep rank, final score, score layers, evidence, and rationale;
- the mobile admin run list/detail reads these historical rows rather than the
  mutable latest-result cache.
- only profile recommendation generation creates these rows; internal Agent
  What-if previews return a temporary `run_id` and do not write them.

The active runtime schema authority is limited to `app/adapters/persistence/sqlalchemy/models/` plus the root `migrations/` history.
