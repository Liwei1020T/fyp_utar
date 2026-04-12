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
  - preview/profile recommendation generation, preference-vector persistence, score caching, explainability, and recommendation logging

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
- The primary derived item-side matrix layer is the NLP/review CSV imported as `source_layer='nlp_review'`
- Older `hybrid_derived` rows remain as compatibility fallback inputs, not as catalog truth
- The current rule engine still returns the existing frontend-facing response shape, but it now reads item-side scores from matrix-backed domain objects rather than from catalog columns

## Recommendation Design Review Summary

The backend review found that the existing FastAPI/use-case/repository layering is clean and should be preserved. The catalog normalization is also already strong: master product truth, official performance, inventory, recommendation matrix rows, user preference vectors, and score cache rows are split into separate tables.

The main weakness was runtime usage. Before this refactor, the public recommender still used a lightweight in-process rule engine and did not actively write `user_preference_matrix` or `recommendation_score_cache`. The safest path was therefore incremental: keep auth, bookings, store ops, catalog endpoints, seed logic, and matrix import stable, then activate the dormant recommendation tables through a recommendation-specific repository and scorer.

## Recommendation Flow

- Profile/onboarding fields are converted into `user_preference_matrix` rows with `source_layer='profile_onboarding_v1'`.
- Active catalog candidates are loaded with official performance, inventory, community metadata, and matrix entries.
- Item features are fused in this order:
  - official/manual performance
  - `nlp_review` matrix rows
  - structured catalog heuristics such as gauge
  - community signals
  - `hybrid_derived` compatibility fallback rows
- The scorer applies:
  - `0.55 * PreferenceMatch`
  - `0.20 * RuleFit`
  - `0.15 * BudgetFit`
  - `0.10 * NLPReviewScore`
- Generated profile recommendations are cached in `recommendation_score_cache` with score breakdown and rationale payloads.
- Cached results are returned through `GET /api/recommendations/{user_id}` and single-item explanations through `GET /api/recommendations/{user_id}/{catalog_id}`.

## AI Boundary

- `ai_service/` remains preserved for standalone compatibility, review analysis, and RAG-style helper logic.
- The active profile recommender now lives in `app/domain/recommendation/scoring.py` and reads normalized catalog/matrix persistence through `app/ports/repositories/recommendation_repository.py`.
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
