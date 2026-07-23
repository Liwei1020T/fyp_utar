# Backend Architecture

## Active Runtime

```text
Mobile App
  -> FastAPI Entrypoints (`app/entrypoints`)
      -> Application Use Cases (`app/use_cases`)
          -> Domain + Ports (`app/domain`, `app/ports`)
              -> SQLAlchemy / JWT Adapters (`app/adapters`)
                  -> PostgreSQL or SQLite test database
```

- `app/` is now the primary runtime package.
- `app/domain/recommendation/scoring.py` is the only recommendation implementation loaded by the unified runtime.
- `ai_service/` is preserved for explicit standalone compatibility checks and is not imported during unified startup.

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
  - JWT, password hashing, and clock adapters; legacy AI adapters remain compatibility-only
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
  - booking creation, retrieval, admin listing, status changes, and service updates
- `booking support`
  - one persisted conversation state per booking, shared messages, read state,
    resolve, and close lifecycle
- `store`
  - business hours, slots, check-in, service queue, store settings, analytics
- `commerce`
  - payment requests, admin verification, and wallet ledger transactions
- `notifications`
  - owned derived event feed, persisted read IDs, and per-user preferences
- `rackets and feedback`
  - owned physical racket passports, completed service history, and one
    structured feedback record per completed booking
- `recommendation`
  - preview/profile recommendation generation, preference-vector persistence, score caching, explainability, and recommendation logging

## Persistence Structure

The old monolithic ORM module was split into per-domain model files:

- `models/user.py`
- `models/profile.py`
- `models/string_catalog_item.py`
  - now owns `brands`, `strings`, `string_catalog_metrics`, `string_catalog_tags`, `string_official_performance`, `inventory_items`, `inventory_movements`, `recommendation_feature_definitions`, `string_recommendation_matrix`, `user_preference_matrix`, and `recommendation_score_cache`
- `models/booking.py`
- `models/booking_conversation.py`
- `models/notification.py`
- `models/racket_feedback.py`
- `models/commerce.py`
  - owns `payments` and append-only `wallet_transactions`
- `models/store_business_hours.py`
- `models/store_settings.py`
- `models/recommendation_log.py`
  - now owns `recommendation_logs`, `recommendation_runs`, and `recommendation_run_items`
- `models/password_reset_code.py`

Alembic targets the SQLAlchemy metadata directly from `app/adapters/persistence/sqlalchemy/`.
The current revision chain has one head at `20260723_0024`.

The current commerce endpoint is a compact transactional boundary in
`commerce_routes.py`. It uses row locks around booking, user-wallet, and
payment transitions. Split it into provider-specific use cases only when an
external gateway/webhook is selected.

## Commerce Flow

- A player creates a booking payment or wallet top-up request.
- External methods remain `pending` until the admin verifies actual receipt.
- Admin verification creates wallet credit exactly once for a top-up.
- Wallet booking payment locks the account row, derives balance from the
  ledger, and writes a debit only when funds are sufficient.
- The mobile app never writes balance or paid status directly.

## Catalog Boundary

- Master catalog truth lives in `strings`
- Community counts/tags live in `string_catalog_metrics` and `string_catalog_tags`
- Official/manual performance lives in `string_official_performance`
- Store pricing and stock live in `inventory_items`
- Recommendation features live in `string_recommendation_matrix`
- The primary derived item-side matrix layer is the V9 NLP/review workbook imported as `source_layer='nlp_review'`
- Older `hybrid_derived` rows remain compatibility data, not master catalog truth
- The active scorer uses official performance plus NLP/review matrix values for PreferenceMatch; structured catalog data is reserved for RuleFit, filtering, and display

## Recommendation Design Review Summary

The backend review found that the existing FastAPI/use-case/repository layering is clean and should be preserved. The catalog normalization is also already strong: master product truth, official performance, inventory, recommendation matrix rows, user preference vectors, score cache rows, and recommendation run history are split into separate tables.

The main weakness was runtime usage. Before this refactor, the public recommender still used a lightweight in-process rule engine and did not actively write `user_preference_matrix` or `recommendation_score_cache`. The safest path was therefore incremental: keep auth, bookings, store ops, catalog endpoints, seed logic, and matrix import stable, then activate the dormant recommendation tables through a recommendation-specific repository and scorer.

## Recommendation Flow

- Profile/onboarding fields are converted into `user_preference_matrix` rows with `source_layer='profile'`.
- Raw 1-to-10 inputs are stored as `raw_score`; backend-normalized weights are stored as `preference_weight`.
- Active catalog candidates are loaded with official performance, inventory, and matrix entries.
- FYP1 uses rule-enhanced, confidence-aware, content-based recommendation with official performance + NLP review feature fusion + budget-tier fit. It does not use collaborative filtering, matrix factorization, embeddings, or interaction-history scoring.
- PreferenceMatch uses only effective item features from official/manual performance and `nlp_review` matrix rows.
- Core recommendation dimensions are `repulsion`, `control`, `durability`, `comfort`, `sound`, `elasticity`, `tension_retention`, and `string_movement`.
- Structured catalog heuristics such as gauge are excluded from PreferenceMatch and used only in RuleFit.
- Per-feature `confidence` from `string_recommendation_matrix` is part of the live fusion input.
- The scorer applies:
  - `0.60 * PreferenceMatch`
  - `0.15 * RuleFit`
  - `0.15 * BudgetFit`
  - `0.10 * ConfidenceScore`
- `BudgetFit` is based on the canonical categorical player budget input: `below_30`, `between_30_50`, and `above_50`.
- Generated profile recommendations are cached in `recommendation_score_cache` with score breakdown, confidence score, artifact version metadata, and rationale payloads.
- Generated recommendations are also persisted into `recommendation_runs` and `recommendation_run_items` for admin inspection and reproducibility.
- Rationale preserves matrix version, feature-source version, artifact generation time, and per-feature source metadata.
- Cached results are returned through `GET /api/recommendations/{user_id}` and single-item explanations through `GET /api/recommendations/{user_id}/{catalog_id}`.

## AI Boundary

- `ai_service/` remains preserved for standalone compatibility, review analysis, and RAG-style helper logic.
- The active profile recommender now lives in `app/domain/recommendation/scoring.py` and reads normalized catalog/matrix persistence through `app/ports/repositories/recommendation_repository.py`.
- Legacy AI adapters and `ai_service.service.RecommendationService` are not wired into unified FastAPI dependencies or startup.

## Validation Contract

Primary validation commands:

```bash
cd backend
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app ai_service tests
./.venv/bin/pytest -v
```
