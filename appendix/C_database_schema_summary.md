# Appendix C: Database Schema Summary

The active backend schema is owned by SQLAlchemy models and Alembic migrations.

Source files:

- `backend/docs/database.md`
- `backend/app/adapters/persistence/sqlalchemy/models/`
- `backend/migrations/versions/`

## Main Tables

| Table | Purpose |
| --- | --- |
| `users` | Stores phone-first identities, usernames, roles, and authentication metadata. |
| `profiles` | Stores player skill level, playing style, budget, tension, frequency, and preference slider values. |
| `brands` | Stores normalized badminton string brand master data. |
| `strings` | Stores master string catalog data such as name, gauge, material, description, and active status. |
| `string_catalog_metrics` | Stores community-facing rating and review count signals. |
| `string_catalog_tags` | Stores multi-tag signals for strings. |
| `string_official_performance` | Stores official or manually curated performance values. |
| `inventory_items` | Stores shop-specific stock, price, availability, and reorder settings. |
| `inventory_movements` | Stores append-only inventory adjustment history. |
| `recommendation_feature_definitions` | Stores canonical recommendation feature metadata. |
| `string_recommendation_matrix` | Stores item-side feature scores from source layers such as `nlp_review`. |
| `user_preference_matrix` | Stores user-side normalized preference vectors. |
| `recommendation_score_cache` | Stores generated recommendation results and score breakdowns per user. |
| `recommendation_logs` | Stores recommendation request and response snapshots. |
| `bookings` | Stores stringing service booking records. |
| `booking_status_history` | Stores audit trail for booking status transitions. |
| `booking_updates` | Stores player/admin comments and optional booking photo metadata. |
| `store_business_hours` | Stores weekly schedule, capacity, slot duration, breaks, and special closed dates. |
| `store_settings` | Stores store contact, address, support copy, policy text, and home-trending strings. |

## Important Design Boundaries

- Master catalog data, inventory data, official performance data, and recommendation-derived data are stored separately.
- NLP review-derived values are stored in `string_recommendation_matrix`, not copied into `strings`.
- User preferences are normalized into `user_preference_matrix` before generating recommendations.
- Recommendation outputs are cached in `recommendation_score_cache` with score breakdowns and explanation payloads.
- Booking status changes are tracked in `booking_status_history` for auditability.
- Booking photos are stored locally under backend upload storage for the FYP demo, while metadata is stored in `booking_updates`.

## Suggested ERD Grouping

For the report appendix, the ERD can be grouped into:

1. User and profile: `users`, `profiles`
2. Catalog and inventory: `brands`, `strings`, `inventory_items`, `inventory_movements`
3. Recommendation: `string_recommendation_matrix`, `user_preference_matrix`, `recommendation_score_cache`, `recommendation_logs`
4. Booking and operations: `bookings`, `booking_status_history`, `booking_updates`, `store_business_hours`, `store_settings`

