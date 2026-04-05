# Backend Architecture

## Active Runtime

```text
Mobile App
  -> FastAPI Entrypoints (`app/entrypoints`)
      -> Application Use Cases (`app/use_cases`)
          -> Domain + Ports (`app/domain`, `app/ports`)
              -> SQLAlchemy / JWT / AI Adapters (`app/adapters`)
                  -> PostgreSQL or SQLite test database
```

- `app/` is now the primary runtime package.
- `stringsense_backend/` remains as a compatibility shell so existing imports, tests, and Alembic wiring keep working while the runtime lives under `app/`.
- `ai_service/` is preserved and reused behind adapter boundaries instead of being deleted.

## Layering Rules

Allowed dependency direction:

- `entrypoints -> use_cases`
- `use_cases -> domain`
- `use_cases -> ports`
- `adapters -> ports`
- `adapters -> domain`

Explicitly avoided:

- route-to-route business imports
- domain objects depending on FastAPI or SQLAlchemy
- use cases depending on ORM models
- adapters pulling business rules from route modules

## Folder Map

- `app/main.py`
  - FastAPI app bootstrap, middleware, exception handlers, startup seeding
- `app/entrypoints/api/routes/`
  - Thin request/response handlers grouped by API surface
- `app/use_cases/`
  - One file per business action or closely related action
- `app/domain/`
  - Pure Python entities, enums, and policies by bounded context
- `app/ports/`
  - Repository and service abstractions
- `app/adapters/persistence/sqlalchemy/`
  - SQLAlchemy session, split ORM models, repositories, seed helpers
- `app/adapters/services/`
  - JWT, password hashing, clock, and AI adapters
- `app/dto/`
  - API request/response models and mapping helpers
- `app/config/`
  - `pydantic-settings` runtime configuration
- `app/shared/`
  - errors, serialization, constants, pagination

## Bounded Contexts

- `auth`
  - registration, login, token parsing, password reset
- `profile`
  - customer preference profile read/write
- `catalog`
  - public strings catalog plus admin inventory controls
- `booking`
  - booking creation, retrieval, admin listing, status changes
- `store`
  - business hours, slots, check-in, service queue, store settings, analytics
- `recommendation`
  - preview/profile recommendation generation and recommendation logging

## Persistence Structure

The old monolithic ORM module was split into per-domain model files:

- `models/user.py`
- `models/profile.py`
- `models/string_catalog_item.py`
- `models/booking.py`
- `models/store_business_hours.py`
- `models/store_settings.py`
- `models/recommendation_log.py`
- `models/password_reset_code.py`

Alembic still targets the same metadata through compatibility imports in `stringsense_backend/db/`.

## AI Boundary

- The public recommendation flow now depends on `RecommendationEngine` through a port.
- `app/adapters/services/ai/recommendation_engine_adapter.py` preserves the current in-process recommendation behavior.
- Review analysis and RAG helpers are preserved as adapters over `ai_service.service.RecommendationService`.

## Compatibility Strategy

These legacy paths remain as wrappers:

- `stringsense_backend/main.py`
- `stringsense_backend/api/*`
- `stringsense_backend/core/*`
- `stringsense_backend/db/*`
- `stringsense_backend/modules/*`

This lets the refactor land incrementally without breaking tests, imports, or migration wiring.

## Validation Contract

Primary validation commands:

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/mypy app stringsense_backend ai_service tests
./.venv/bin/pytest -q
```
