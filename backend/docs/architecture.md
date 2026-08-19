# Backend Architecture

## Active Runtime

```text
Mobile App
  -> FastAPI Entrypoints (`app/entrypoints`)
      -> Application Use Cases (`app/use_cases`)
          -> Domain + Ports (`app/domain`, `app/ports`)
      -> SQLAlchemy / JWT Adapters (`app/adapters`)
          -> Domain + Ports
          -> PostgreSQL or SQLite test database
```

- `app/` is now the primary runtime package.
- `app/domain/recommendation/scoring.py` is the only recommendation implementation loaded by the unified runtime.
- `ai_service/` is preserved for explicit standalone compatibility checks and is not imported during unified startup.

## Layering Rules

Allowed dependency direction:

- `entrypoints -> use_cases`
- `entrypoints -> adapters` for dependency composition and compact
  single-adapter persistence modules
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
  - Request/response handlers grouped by API surface; multi-step reusable
    behavior delegates to use cases. Admin engagement and analytics have
    separate route modules so their SQL and provider helpers stay local.
- `app/use_cases/`
  - One file per business action or closely related action
- `app/domain/`
  - Pure Python entities, enums, and policies by bounded context
- `app/ports/`
  - Repository and service abstractions
- `app/adapters/persistence/sqlalchemy/`
  - SQLAlchemy session, split ORM models, repositories, seed helpers
- `app/adapters/services/`
  - JWT, password hashing, and clock adapters
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
- `agent`
  - authenticated grounded answers, exact-run recommendation explanation,
    bounded read-only tools, V11 What-if preview, and explicit support handoff

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
The current revision chain has one head at `20260731_0026`.

## Transaction Contract

- `get_db()` owns the request transaction: every FastAPI `get_db` dependency is
  function-scoped, so commit/rollback and transaction effects finish before
  `http.response.start`; the session closes in all cases.
- `app/shared/transaction_effects.py` journals filesystem changes against that
  session: newly written upload files are removed on rollback or commit
  failure, while replaced/removed old files run only after a successful commit.
- Repositories remain commit-free. Route-local persistence calls `flush()` when
  generated IDs or constraint checks are needed; notification send/resend is
  the sole current exception, explicitly committing `pending` before provider
  I/O.
- Multi-repository use cases compose writes without a transaction-manager port.
  Failure-injection tests prove profile, recommendation, reset, and check-in
  writes roll back together.
- Expected invalid reset-code attempts return an error result to the route so
  the security attempt counter is committed before the route returns HTTP 400.

Fresh store defaults are deliberately non-operational: every business-hours
day starts closed and store contact/address/pricing remain unconfigured until
an administrator saves real values.

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
- The approved catalog JSON is bootstrap-only: it is read when `strings` is
  empty, while later startups use persisted catalog rows.
- Community counts/tags live in `string_catalog_metrics` and `string_catalog_tags`
- Official/manual performance lives in `string_official_performance`
- Store pricing and stock live in `inventory_items`
- Recommendation features live in `string_recommendation_matrix`
- The primary derived item-side matrix layer is the V9 NLP/review workbook imported as `source_layer='nlp_review'`
- The workbook is an optional startup import. If it is absent, persisted catalog
  and official-performance data remain usable and health reports
  `catalog_fallback`; an imported matrix remains available from the database
  even when the source workbook is later offline. Health reports the persisted
  `nlp_review` row count without duplicating artifact metadata on every row.
- A malformed startup artifact is isolated in a savepoint: its partial writes
  roll back, the persisted matrix remains active, and startup logs the rejection.
- Manual artifact parsing/validation failures return HTTP 400; database and
  filesystem failures are not converted into artifact errors.
- Older `hybrid_derived` rows remain compatibility data, not master catalog truth
- The active scorer uses official performance plus NLP/review matrix values for PreferenceMatch; structured catalog data is reserved for RuleFit, filtering, and display

## Recommendation Design Review Summary

The backend review found that the existing FastAPI/use-case/repository layering is clean and should be preserved. The catalog normalization is also already strong: master product truth, official performance, inventory, recommendation matrix rows, user preference vectors, score cache rows, and recommendation run history are split into separate tables.

The main weakness was runtime usage. Before this refactor, the public recommender still used a lightweight in-process rule engine and did not actively write `user_preference_matrix` or `recommendation_score_cache`. The safest path was therefore incremental: keep auth, bookings, store ops, catalog endpoints, seed logic, and matrix import stable, then activate the dormant recommendation tables through a recommendation-specific repository and scorer.

## Recommendation Flow

- Profile/onboarding fields are converted into `user_preference_matrix` rows with `source_layer='profile'`.
- Raw 1-to-10 inputs are stored as `raw_score`; backend-normalized weights are stored as `preference_weight`.
- Active catalog candidates are loaded with official performance, inventory, and matrix entries.
- FYP1 uses rule-enhanced content recommendation with fixed official/NLP fusion,
  profile rules, and bounded confirmed-feedback calibration. Exact-racket
  interaction history receives a bounded CF weight only after three independent
  exact-model supporters; sparse cases retain the base score. Matrix factorization
  and embeddings are not used.
- PreferenceMatch uses only effective item features from official/manual performance and `nlp_review` matrix rows.
- Core recommendation dimensions are `repulsion`, `control`, `durability`, `comfort`, `sound`, `elasticity`, `tension_retention`, `string_movement`, and `value_for_money`.
- Structured catalog heuristics such as gauge are excluded from PreferenceMatch and used only in RuleFit.
- Official and NLP values use fixed equal fusion when both exist; a single available source is used directly, and the prior is used only when both are missing.
- The scorer ranks with `(0.75 * PreferenceMatch + 0.15 * RuleFit) / 0.90`.
- Gauge, official feel, and structured recent goal are soft RuleFit inputs; catalog price is descriptive only.
- Generated profile recommendations are cached in `recommendation_score_cache` with score breakdown and rationale payloads.
- Generated recommendations are also persisted into `recommendation_runs` and `recommendation_run_items` for admin inspection and reproducibility.
- Rationale preserves the actual official/NLP values and the fixed source contribution used for each feature.
- Cached results are returned through `GET /api/recommendations/{user_id}` and single-item explanations through `GET /api/recommendations/{user_id}/{catalog_id}`.

## AI Boundary

- `ai_service/` remains preserved for standalone compatibility, review analysis, and RAG-style helper logic.
- The active profile recommender now lives in `app/domain/recommendation/scoring.py` and reads normalized catalog/matrix persistence through `app/ports/repositories/recommendation_repository.py`.
- The unified FYP-scoped Agent lives in `app/use_cases/agent`, calls DeepSeek only
  through `app/adapters/services/agent`, and supports four-question guided
  selection, exact-run explanation, verified in-stock alternatives, and one
  read-only admin operations summary. The model cannot write application state
  or replace V11 scoring. Broader completed tools and admin confirmation handlers
  remain preserved behind inactive allowlist entries.
- Exact recommendation explanations are owner-scoped by persisted `run_id`;
  source metadata is collected server-side from successful tool calls.
- The former unified-runtime legacy AI adapters were removed.
  `ai_service.service.RecommendationService` remains isolated inside the
  explicit standalone compatibility package and is not wired into unified
  FastAPI dependencies or startup.

## Authentication Abuse Boundary

Login, reset-code request, and reset submission use a small sliding-window
limiter keyed by the server-observed client address plus normalized phone
number. The limiter is process-local for the current single-process FYP
deployment; a multi-worker deployment must enforce the equivalent policy at a
shared gateway or distributed store.

## Notification Delivery Boundary

Admin remote notification requests use an explicit two-phase boundary: the route
commits `pending` before provider I/O, then the provider runs with no original
request transaction active. The outcome is committed, refreshed, and read in a
separate short SQLAlchemy session, and enabled send/resend responses return the
truthful final `sent`/`failed` state. A queue is intentionally out of scope for
the current single-process FYP deployment. The persisted row also supplies the
App notification feed; the selected FYP remote provider is OpenWA.
The same persisted-delivery path powers completed-booking feedback follow-ups:
the single-process scheduler checks immediately at startup and hourly, sends at
day 7 and once more at day 10 only while feedback is absent, and deduplicates by
booking route plus follow-up title.

## Validation Contract

Primary validation commands:

```bash
cd backend
./scripts/alembic heads
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/mypy app ai_service tests
./.venv/bin/pytest -v
```
