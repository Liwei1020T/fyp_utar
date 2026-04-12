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
  - normalized master catalog, admin inventory controls, official performance persistence, and recommendation matrix inputs
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
  - now owns `brands`, `strings`, `string_catalog_metrics`, `string_catalog_tags`, `string_official_performance`, `inventory_items`, `inventory_movements`, `recommendation_feature_definitions`, `string_recommendation_matrix`, `user_preference_matrix`, and `recommendation_score_cache`
- `models/booking.py`
- `models/store_business_hours.py`
- `models/store_settings.py`
- `models/recommendation_log.py`
- `models/password_reset_code.py`

Alembic targets the SQLAlchemy metadata directly from `app/adapters/persistence/sqlalchemy/`.

## Catalog Boundary

- Master catalog truth lives in `strings`
- Community counts/tags live in `string_catalog_metrics` and `string_catalog_tags`
- Official/manual performance lives in `string_official_performance`
- Store pricing and stock live in `inventory_items`
- Recommendation features live in `string_recommendation_matrix`
- The current rule engine still returns the existing frontend-facing response shape, but it now reads item-side scores from matrix-backed domain objects rather than from catalog columns

## AI Boundary

- The public recommendation flow now depends on `RecommendationEngine` through a port.
- `app/adapters/services/ai/recommendation_engine_adapter.py` preserves the current in-process recommendation behavior while reading compatibility aspect scores from the normalized catalog domain mapping.
- Review analysis and RAG helpers are preserved as adapters over `ai_service.service.RecommendationService`.

## Validation Contract

Primary validation commands:

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app ai_service tests
./.venv/bin/pytest -v
```
