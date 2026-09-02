# Appendix C: Database Schema Summary

The active backend schema is owned by SQLAlchemy models and Alembic migrations.
At head `20260902_0044`, it contains 32 application tables plus the
`alembic_version` migration metadata table. The source JSON may contain 33
strings for offline provenance, but only the approved 12 are seeded into these
runtime tables.

Source files:

- `backend/docs/database.md`
- `backend/app/adapters/persistence/sqlalchemy/models/`
- `backend/migrations/versions/`

## Main Tables

| Table | Purpose |
| --- | --- |
| `users` | Stores phone-first identities, usernames, roles, and authentication metadata. |
| `password_reset_codes` | Stores hashed, expiring password-reset verification codes. |
| `profiles` | Stores player skill level, playing style, budget, tension, frequency, and preference slider values. |
| `brands` | Stores normalized badminton string brand master data. |
| `strings` | Stores master string catalog data such as name, gauge, material, description, and active status. |
| `string_catalog_metrics` | Stores feedback-facing rating and review count signals. |
| `string_catalog_tags` | Stores multi-tag signals for strings. |
| `string_official_performance` | Stores official or manually curated performance values. |
| `inventory_items` | Stores shop-specific stock, price, availability, and reorder settings. |
| `inventory_movements` | Stores append-only inventory adjustment history. |
| `recommendation_feature_definitions` | Stores canonical recommendation feature metadata. |
| `string_recommendation_matrix` | Stores item-side feature scores from source layers such as `nlp_review`. |
| `user_preference_matrix` | Stores user-side normalized preference vectors. |
| `recommendation_score_cache` | Stores generated recommendation results and score breakdowns per user. |
| `recommendation_runs` | Stores immutable request/profile snapshots and artifact versions for admin audit. |
| `recommendation_run_items` | Stores ranked score layers and rationales for each historical run. |
| `racket_model_catalog` | Stores the admin-managed racket models available to player racket selectors. |
| `bookings` | Stores stringing service booking records. |
| `check_in_tokens` | Stores expiring, one-time hashed booking check-in tokens. |
| `booking_status_history` | Stores audit trail for booking status transitions. |
| `booking_updates` | Stores player/admin comments and optional booking photo metadata. |
| `booking_conversations` | Stores one support-thread state and read timestamps per booking. |
| `support_conversations` | Stores the reusable booking-free player support thread state. |
| `support_conversation_messages` | Stores messages in booking-free support threads. |
| `rackets` | Stores user-owned physical racket passports. |
| `booking_feedback` | Stores one structured feedback row per completed booking. |
| `notifications` | Stores persisted in-app notifications and the latest optional OpenWA delivery status. |
| `notification_reads` | Stores stable derived event IDs read by each user. |
| `payments` | Stores booking payments and wallet top-ups with admin-verification state. |
| `wallet_transactions` | Stores the append-only wallet credit/debit ledger. |
| `store_business_hours` | Stores weekly schedule, capacity, slot duration, breaks, and special closed dates. |
| `store_settings` | Stores store contact, address, support copy, policy text, and the player-facing Featured strings selection. |

## Important Design Boundaries

- Master catalog data, inventory data, official performance data, and recommendation-derived data are stored separately.
- NLP review-derived values are stored in `string_recommendation_matrix`, not copied into `strings`.
- User preferences are normalized into `user_preference_matrix` before generating recommendations.
- Recommendation outputs are cached in `recommendation_score_cache` with score breakdowns and explanation payloads.
- Only profile recommendation generation writes `recommendation_runs` and
  `recommendation_run_items`; internal Agent What-if previews return a temporary
  run ID and do not write recommendation data.
- Booking status changes are tracked in `booking_status_history` for auditability.
- Booking photos are stored locally under backend upload storage for the FYP demo, while metadata is stored in `booking_updates`.
- Conversation messages reuse `booking_updates` with a conversation channel,
  while `booking_conversations` owns thread lifecycle and read state.
- Wallet balance is derived from `wallet_transactions`; clients never write a
  balance counter or paid status directly.

## Suggested ERD Grouping

For the report appendix, the ERD can be grouped into:

1. User and profile: `users`, `profiles`, `password_reset_codes`
2. Catalog and inventory: `brands`, `strings`, `racket_model_catalog`,
   `inventory_items`, `inventory_movements`
3. Recommendation: `string_recommendation_matrix`, `user_preference_matrix`,
   `recommendation_score_cache`,
   `recommendation_runs`, `recommendation_run_items`
4. Booking and support: `bookings`, `check_in_tokens`,
   `booking_status_history`, `booking_updates`, `booking_conversations`,
   `support_conversations`, `support_conversation_messages`, `rackets`,
   `booking_feedback`
5. Commerce and notifications: `payments`, `wallet_transactions`,
   `notifications`, `notification_reads`
6. Store operations: `store_business_hours`, `store_settings`

The database table named `trending_string_ids` is an internal persisted field
for the player-facing Featured strings selection; it does not claim that the
values are statistically trending.
