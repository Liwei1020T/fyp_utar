# Clean Architecture Migration Map

## Runtime Entry

- Old: `stringsense_backend/main.py`
- New: `app/main.py`
- Compatibility: `stringsense_backend/main.py` re-exports the new app

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
  - `app/use_cases/recommendation/list_recommendation_logs.py`

## ORM and Repositories

- Old: `stringsense_backend/db/models.py`
- New: split model files under `app/adapters/persistence/sqlalchemy/models/`

- Old: route modules performed direct SQLAlchemy queries
- New: SQLAlchemy access is isolated in repository adapters under `app/adapters/persistence/sqlalchemy/repositories/`

## Security and AI

- Old: `stringsense_backend/core/security.py`
- New:
  - `app/adapters/services/security/pbkdf2_password_hasher.py`
  - `app/adapters/services/security/jwt_token_service.py`

- Old: `stringsense_backend/modules/ai.py`
- New: `app/adapters/services/ai/recommendation_engine_adapter.py`

## Shared / Config

- Old: `stringsense_backend/core/config.py`, `errors.py`, `http.py`, `serialization.py`
- New:
  - `app/config/settings.py`
  - `app/shared/errors.py`
  - `app/shared/http.py`
  - `app/shared/serialization.py`
  - `app/shared/pagination.py`
