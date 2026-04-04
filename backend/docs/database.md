# Database Ownership and Schema Strategy

## Source of Truth

SQLAlchemy models in [models.py](../stringsense_backend/db/models.py) plus Alembic revisions in [migrations](../migrations) are now the active schema source of truth for the backend.

The initial unified-backend migration is:

- [20260404_0001_unified_python_backend.py](../migrations/versions/20260404_0001_unified_python_backend.py)

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

### `string_catalog_items`

Stores approved catalog string entries plus their normalized recommendation aspect scores.
Also carries single-store inventory fields:

- `stock_level`
- `admin_note`
- `is_active` as the public availability gate

### `store_business_hours`

Stores the single-store weekly schedule plus special closed dates used to generate booking slot availability.

### `store_settings`

Stores the single-store support copy, policy text, contact details, and other admin-facing settings used by the operations UI.

### `bookings`

Stores service-tracking bookings only. Slot conflict detection remains intentionally out of scope.
Current lifecycle values are `awaiting_dropoff`, `in_progress`, `ready_for_collection`, `completed`, `cancelled`, and `rejected`.

### `booking_status_history`

Stores booking status transitions plus optional admin operator notes for auditability.

### `recommendation_logs`

Stores request snapshots, result snapshots, and `algorithm_version`.

## Legacy Schema References

The following are no longer active schema owners:

- [nest-api/prisma/schema.prisma](../nest-api/prisma/schema.prisma)
- [archive/python_business_backend/app/db/models.py](../archive/python_business_backend/app/db/models.py)
- [archive/python_business_backend/alembic](../archive/python_business_backend/alembic)

They remain reference material only and must not be treated as runtime schema authorities.
