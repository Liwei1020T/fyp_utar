# Clean Architecture Migration Map

## Runtime Entry

- Old: `stringsense_backend/main.py`
- New: `app/main.py`
- Status: legacy compatibility shell removed after imports, tests, and Alembic were rewired

## API Layer

- Old: `stringsense_backend/api/router.py`
- New: `app/entrypoints/api/router.py`

- Old: `stringsense_backend/modules/auth.py`
- New: `app/entrypoints/api/routes/auth_routes.py`

- Old: `stringsense_backend/modules/profile.py`
- New: `app/entrypoints/api/routes/profile_routes.py`

- Old: `stringsense_backend/modules/strings.py`
- New: `app/entrypoints/api/routes/catalog_routes.py`

- Old: `stringsense_backend/modules/bookings.py`
- New: `app/entrypoints/api/routes/booking_routes.py`

- Old: `stringsense_backend/modules/recommendations.py`
- New: `app/entrypoints/api/routes/recommendation_routes.py`

- Old: `stringsense_backend/modules/admin.py`
- New: `app/entrypoints/api/routes/admin_routes.py`

- Old: `stringsense_backend/modules/store_ops.py`
- New: `app/entrypoints/api/routes/store_routes.py` plus store/admin actions in `app/entrypoints/api/routes/admin_routes.py`

Current post-migration route modules with no legacy one-file equivalent:

- `app/entrypoints/api/routes/commerce_routes.py`
- `app/entrypoints/api/routes/notification_routes.py`
- `app/entrypoints/api/routes/booking_conversation_routes.py`
- `app/entrypoints/api/routes/racket_feedback_routes.py`

## Business Logic

- Old: booking transition rules in route helpers and shared enums in `stringsense_backend/core/domain.py`
- New: `app/domain/booking/enums.py` and `app/domain/booking/policies.py`

- Old: store slot, queue, check-in, and analytics logic inside `stringsense_backend/modules/store_ops.py`
- New:
  - `app/use_cases/store/list_slots.py`
  - `app/use_cases/store/lookup_checkin.py`
  - `app/use_cases/store/confirm_checkin.py`
  - `app/use_cases/store/get_queue.py`
  - `app/use_cases/store/get_store_analytics.py`

- Old: recommendation orchestration inside `stringsense_backend/modules/recommendations.py`
- New:
  - `app/use_cases/recommendation/generate_recommendation.py`

## ORM and Repositories

- Old: `stringsense_backend/db/models.py`
- New: split model files under `app/adapters/persistence/sqlalchemy/models/`

- Old: route modules mixed reusable domain rules with direct SQLAlchemy queries
- New: reusable and multi-repository behavior uses ports plus repository
  adapters under `app/adapters/persistence/sqlalchemy/repositories/`.
  Compact single-provider CRUD/ledger modules may remain in the entrypoint when
  adding a one-implementation port would only add pass-through boilerplate.

- `app/adapters/persistence/sqlalchemy/session.py:get_db` owns commit/rollback
  for every request. Repositories and route-local persistence only flush, so
  multi-repository use cases remain atomic without a pass-through transaction
  manager abstraction.

## Security and Recommendation

- Old: `stringsense_backend/core/security.py`
- New:
  - `app/adapters/services/security/pbkdf2_password_hasher.py`
  - `app/adapters/services/security/jwt_token_service.py`

- Old: `stringsense_backend/modules/ai.py`
- Active recommendation: `app/domain/recommendation/scoring.py`

## Shared / Config

- Old: `stringsense_backend/core/config.py`, `errors.py`, `http.py`, `serialization.py`
- New:
  - `app/config/settings.py`
  - `app/shared/errors.py`
  - `app/shared/http.py`
  - `app/shared/serialization.py`
  - `app/shared/pagination.py`
