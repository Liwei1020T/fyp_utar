# StringSence Codebase Map

Use this file as the first-stop map before opening source files. It does not
replace the code, but it should help future development avoid reading every file
just to find the right ownership boundary.

## Reading Order

1. Start here for ownership, entry points, and "where do I change this?"
2. Read [README.md](../README.md) for setup and cross-workspace quick start.
3. Read [docs/fyp1-scope.md](./fyp1-scope.md) before changing visible demo scope.
4. Read [mobile/docs/frontend-architecture.md](../mobile/docs/frontend-architecture.md) before changing Expo screens, state, or UI primitives.
5. Read [backend/docs/architecture.md](../backend/docs/architecture.md), [backend/docs/api-contract.md](../backend/docs/api-contract.md), and [backend/docs/database.md](../backend/docs/database.md) before changing API behavior.
6. Read [ml/nlp-workbench/README.md](../ml/nlp-workbench/README.md) before regenerating AI/NLP artifacts.

## Workspace Roots

| Path | Purpose | Open When |
| --- | --- | --- |
| [AGENTS.md](../AGENTS.md) | Repo-specific rules, validation commands, architecture boundaries, and done criteria. | Starting any task in this repo. |
| [README.md](../README.md) | Human quick start for the integrated mobile, backend, and NLP workspace. | Onboarding, demo setup, backend/mobile connection setup. |
| [compose.yaml](../compose.yaml) | Local Postgres 16 service on host port `55432`. | Backend needs local database state. |
| [docs/README.md](./README.md) | Workspace documentation index. | Finding existing docs. |
| [docs/fyp1-scope.md](./fyp1-scope.md) | FYP1 included/deferred scope, recommendation positioning, and demo proof. | Changing visible demo scope or deciding whether a feature is FYP1 or FYP2. |
| [docs/codebase-map.md](./codebase-map.md) | This low-token source map. | Deciding which source files are worth opening. |

Local archive files such as `backend.zip`, `ml.zip`, `stringsence.zip`, and
notebook export folders are snapshots or generated handoff artifacts. Do not
treat them as active source unless a task explicitly asks to restore or compare
against them.

## Mobile App

Mobile lives in [mobile](../mobile). It is an Expo Router React Native app using
TypeScript, HeroUI Native, Uniwind, Zustand, React Query, React Hook Form, and
Zod.

### Mobile Config And Runtime

| Path | Purpose | Notes |
| --- | --- | --- |
| [mobile/package.json](../mobile/package.json) | Expo scripts and dependency versions. | Main scripts are `npm run web`, `npm run ios`, `npm run android`; typecheck uses `npx tsc --noEmit`. |
| [mobile/.nvmrc](../mobile/.nvmrc) | Node version pin. | Run `nvm use` before installing or running the app. |
| [mobile/app.json](../mobile/app.json) | Expo app metadata. | Update when app name, icons, or Expo config changes. |
| [mobile/babel.config.js](../mobile/babel.config.js) | Expo/Babel setup. | Keeps worklet and import-meta compatibility stable. |
| [mobile/metro.config.js](../mobile/metro.config.js) | Metro bundler plus Uniwind integration. | Must continue pointing at `global.css`. |
| [mobile/global.css](../mobile/global.css) | Uniwind/HeroUI Native global style entry. | Imported from the root layout. |
| [mobile/tailwind.config.js](../mobile/tailwind.config.js) | Tailwind/Uniwind design tokens. | Change when global utility tokens change. |
| [mobile/tsconfig.json](../mobile/tsconfig.json) | TypeScript compiler config. | Use for path/type strictness changes. |
| [mobile/uniwind-types.d.ts](../mobile/uniwind-types.d.ts) | Uniwind type declarations. | Usually not touched. |

### Mobile Routing

| Path | Purpose |
| --- | --- |
| [mobile/app/_layout.tsx](../mobile/app/_layout.tsx) | Composition root: imports `global.css`, creates `QueryClient`, wraps `GestureHandlerRootView` and `HeroUINativeProvider`, and renders the root stack. |
| [mobile/app/index.tsx](../mobile/app/index.tsx) | Initial redirect based on current user role/session. |
| [mobile/app/auth/_layout.tsx](../mobile/app/auth/_layout.tsx) | Auth stack layout and redirect guard for already-authenticated users. |
| [mobile/app/auth/welcome.tsx](../mobile/app/auth/welcome.tsx) | Role-aware welcome/entry screen. |
| [mobile/app/auth/login.tsx](../mobile/app/auth/login.tsx) | Login form; player and seeded admin login can hit the backend auth flow. |
| [mobile/app/auth/register.tsx](../mobile/app/auth/register.tsx) | Player registration form against backend session bridge. |
| [mobile/app/auth/forgot-password.tsx](../mobile/app/auth/forgot-password.tsx) | Password reset code request/reset flow. |
| [mobile/app/player/_layout.tsx](../mobile/app/player/_layout.tsx) | Player route-group guard. |
| [mobile/app/player/(tabs)/_layout.tsx](../mobile/app/player/%28tabs%29/_layout.tsx) | Player tab shell. |
| [mobile/app/player/(tabs)/home.tsx](../mobile/app/player/%28tabs%29/home.tsx) | Player dashboard and quick actions. |
| [mobile/app/player/(tabs)/strings.tsx](../mobile/app/player/%28tabs%29/strings.tsx) | String catalog browsing and sorting. |
| [mobile/app/player/(tabs)/recommend.tsx](../mobile/app/player/%28tabs%29/recommend.tsx) | Recommendation input form and backend recommendation trigger. |
| [mobile/app/player/(tabs)/bookings.tsx](../mobile/app/player/%28tabs%29/bookings.tsx) | Player booking list and filtering. |
| [mobile/app/player/(tabs)/chat.tsx](../mobile/app/player/%28tabs%29/chat.tsx) | Player chat thread list. |
| [mobile/app/player/(tabs)/profile.tsx](../mobile/app/player/%28tabs%29/profile.tsx) | Player profile overview. |
| [mobile/app/player/bookings/new.tsx](../mobile/app/player/bookings/new.tsx) | Booking creation form and slot/string selection. |
| [mobile/app/player/bookings/summary.tsx](../mobile/app/player/bookings/summary.tsx) | Booking draft confirmation summary. |
| [mobile/app/player/bookings/[id].tsx](../mobile/app/player/bookings/[id].tsx) | Player booking detail. |
| [mobile/app/player/bookings/[id]/tracking.tsx](../mobile/app/player/bookings/[id]/tracking.tsx) | Service timeline screen. |
| [mobile/app/player/payments/[bookingId].tsx](../mobile/app/player/payments/[bookingId].tsx) | Payment method selection and payment simulation. |
| [mobile/app/player/payments/[bookingId]/result.tsx](../mobile/app/player/payments/[bookingId]/result.tsx) | Payment result screen. |
| [mobile/app/player/strings/[id].tsx](../mobile/app/player/strings/[id].tsx) | String detail screen. |
| [mobile/app/player/strings/compare.tsx](../mobile/app/player/strings/compare.tsx) | String comparison flow. |
| [mobile/app/player/recommend/results.tsx](../mobile/app/player/recommend/results.tsx) | Recommendation result list. |
| [mobile/app/player/recommend/explain/[id].tsx](../mobile/app/player/recommend/explain/[id].tsx) | Recommendation explanation detail. |
| [mobile/app/player/profile/edit.tsx](../mobile/app/player/profile/edit.tsx) | Editable recommendation/player profile form. |
| [mobile/app/player/chat/[id].tsx](../mobile/app/player/chat/[id].tsx) | Player chat detail. |
| [mobile/app/player/chatbot.tsx](../mobile/app/player/chatbot.tsx) | Legacy redirect for chatbot route compatibility. |
| [mobile/app/player/check-in.tsx](../mobile/app/player/check-in.tsx) | Player QR/check-in reference screen. |
| [mobile/app/player/feedback/[bookingId].tsx](../mobile/app/player/feedback/[bookingId].tsx) | Post-service feedback screen. |
| [mobile/app/player/notifications.tsx](../mobile/app/player/notifications.tsx) | Notification list. |
| [mobile/app/player/notifications/preferences.tsx](../mobile/app/player/notifications/preferences.tsx) | Notification settings. |
| [mobile/app/player/rackets.tsx](../mobile/app/player/rackets.tsx) | Racket passport list. |
| [mobile/app/player/rackets/[id].tsx](../mobile/app/player/rackets/[id].tsx) | Racket passport detail. |
| [mobile/app/player/wallet.tsx](../mobile/app/player/wallet.tsx) | Wallet balance and transaction screen. |
| [mobile/app/player/wallet/top-up.tsx](../mobile/app/player/wallet/top-up.tsx) | Wallet top-up simulation. |
| [mobile/app/admin/_layout.tsx](../mobile/app/admin/_layout.tsx) | Admin route-group guard. |
| [mobile/app/admin/(tabs)/_layout.tsx](../mobile/app/admin/%28tabs%29/_layout.tsx) | Admin tab shell. |
| [mobile/app/admin/(tabs)/dashboard.tsx](../mobile/app/admin/%28tabs%29/dashboard.tsx) | Admin operational dashboard. |
| [mobile/app/admin/(tabs)/bookings.tsx](../mobile/app/admin/%28tabs%29/bookings.tsx) | Admin booking management list. |
| [mobile/app/admin/(tabs)/inventory.tsx](../mobile/app/admin/%28tabs%29/inventory.tsx) | Admin inventory list. |
| [mobile/app/admin/(tabs)/chat.tsx](../mobile/app/admin/%28tabs%29/chat.tsx) | Admin chat queue. |
| [mobile/app/admin/(tabs)/analytics.tsx](../mobile/app/admin/%28tabs%29/analytics.tsx) | Admin analytics view. |
| [mobile/app/admin/bookings/[id].tsx](../mobile/app/admin/bookings/[id].tsx) | Admin booking detail and status updates. |
| [mobile/app/admin/inventory/[id].tsx](../mobile/app/admin/inventory/[id].tsx) | Admin inventory detail edits. |
| [mobile/app/admin/business-hours.tsx](../mobile/app/admin/business-hours.tsx) | Store business hours editor. |
| [mobile/app/admin/check-in.tsx](../mobile/app/admin/check-in.tsx) | Admin check-in lookup and confirmation. |
| [mobile/app/admin/service-queue.tsx](../mobile/app/admin/service-queue.tsx) | Admin service queue lanes. |
| [mobile/app/admin/payments.tsx](../mobile/app/admin/payments.tsx) | Payment monitoring screen. |
| [mobile/app/admin/settings.tsx](../mobile/app/admin/settings.tsx) | Limited FYP1 store settings editor for store name, contact, address, support text, booking notes, and booking policy text. |
| [mobile/app/admin/chat/[id].tsx](../mobile/app/admin/chat/[id].tsx) | Admin chat detail. |

### Mobile State, Services, And Types

| Path | Purpose | Open When |
| --- | --- | --- |
| [mobile/store/appStore.ts](../mobile/store/appStore.ts) | Zustand source of truth for session state, live player/admin bridge data, mock state, booking/payment mutations, chat, wallet, notifications, admin settings, and selector hooks. | UI state is stale, screen needs a new mutation, or mock/live session behavior changes. |
| [mobile/services/backendApi.ts](../mobile/services/backendApi.ts) | Fetch wrapper and typed backend endpoint methods; uses `EXPO_PUBLIC_API_BASE_URL` with a 12s timeout. | Adding or changing live backend calls. |
| [mobile/services/backendMappers.ts](../mobile/services/backendMappers.ts) | Converts backend snake_case DTOs into mobile domain models and builds backend payloads from mobile state. | Backend contract changes or mobile/backend field names diverge. |
| [mobile/services/mockAppService.ts](../mobile/services/mockAppService.ts) | Synchronous read helpers over mock datasets. | Mock-first screens need lookup or derived data. |
| [mobile/types/domain.ts](../mobile/types/domain.ts) | Canonical mobile domain types: users, strings, bookings, recommendations, payments, chat, notifications, rackets, business hours, wallet, settings. | Any screen/domain shape changes. |
| [mobile/types/backend.ts](../mobile/types/backend.ts) | Backend API response/payload TypeScript interfaces. | Backend API contract changes. |
| [mobile/lib/navigation.ts](../mobile/lib/navigation.ts) | Role home route helpers. | Role landing behavior changes. |
| [mobile/lib/formatters.ts](../mobile/lib/formatters.ts) | Shared display formatting helpers. | Dates, currency, or labels need consistent formatting. |

### Mobile UI Components

| Path | Purpose |
| --- | --- |
| [mobile/components/ui/heroui.tsx](../mobile/components/ui/heroui.tsx) | Thin compatibility wrappers over HeroUI Native primitives and `cn`. |
| [mobile/components/ui/theme.ts](../mobile/components/ui/theme.ts) | App color/layout tokens and status-to-chip variant mapping. |
| [mobile/components/ui/AppButton.tsx](../mobile/components/ui/AppButton.tsx) | Branded button primitive. |
| [mobile/components/ui/AppCard.tsx](../mobile/components/ui/AppCard.tsx) | Branded card primitive. |
| [mobile/components/ui/AppChip.tsx](../mobile/components/ui/AppChip.tsx) | Status/label chip primitive. |
| [mobile/components/ui/AppIconButton.tsx](../mobile/components/ui/AppIconButton.tsx) | Icon button primitive. |
| [mobile/components/ui/AppInput.tsx](../mobile/components/ui/AppInput.tsx) | Text input primitive. |
| [mobile/components/shared/AppScreen.tsx](../mobile/components/shared/AppScreen.tsx) | Shared screen container and bottom inset helper. |
| [mobile/components/shared/AppSection.tsx](../mobile/components/shared/AppSection.tsx) | Section wrapper for grouped content. |
| [mobile/components/shared/AppDetailList.tsx](../mobile/components/shared/AppDetailList.tsx) | Key/value detail rows. |
| [mobile/components/roles/RoleGuard.tsx](../mobile/components/roles/RoleGuard.tsx) | Central role-based route guard. |
| [mobile/components/auth/AuthShell.tsx](../mobile/components/auth/AuthShell.tsx) | Shared auth-screen layout. |
| [mobile/components/booking/BookingCard.tsx](../mobile/components/booking/BookingCard.tsx) | Booking summary card. |
| [mobile/components/booking/SlotPicker.tsx](../mobile/components/booking/SlotPicker.tsx) | Slot selection UI. |
| [mobile/components/tracking/TrackingTimeline.tsx](../mobile/components/tracking/TrackingTimeline.tsx) | Booking status timeline UI. |
| [mobile/components/chat/ConversationCard.tsx](../mobile/components/chat/ConversationCard.tsx) | Chat thread card. |
| [mobile/components/chat/ChatBubble.tsx](../mobile/components/chat/ChatBubble.tsx) | Chat message bubble. |
| [mobile/components/payment/PaymentMethodCard.tsx](../mobile/components/payment/PaymentMethodCard.tsx) | Payment option card. |
| [mobile/components/rackets/RacketPassportCard.tsx](../mobile/components/rackets/RacketPassportCard.tsx) | Racket passport summary card. |
| [mobile/components/analytics/MetricStatCard.tsx](../mobile/components/analytics/MetricStatCard.tsx) | Admin analytics metric card. |

### Mobile Mock And Visual Assets

| Path | Purpose |
| --- | --- |
| [mobile/mocks](../mobile/mocks) | Mock datasets by domain: users, strings, bookings, payments, slots, rackets, notifications, chats, analytics, business hours, settings, wallet. |
| [mobile/mocks/index.ts](../mobile/mocks/index.ts) | Re-export surface for mock modules. |
| [mobile/assets](../mobile/assets) | Expo icon/splash/favicon assets. |
| [mobile/output](../mobile/output) | Tracked visual screenshots and Playwright snapshots for UI reference. Treat as reference artifacts, not runtime code. |
| [mobile/tests/heroui-compat.smoke.tsx](../mobile/tests/heroui-compat.smoke.tsx) | Smoke test for HeroUI compatibility wrappers. |

## Backend

Backend lives in [backend](../backend). The active runtime is FastAPI under
`backend/app`; `backend/ai_service` is preserved for reusable AI logic and
compatibility.

### Backend Config And Runtime

| Path | Purpose | Notes |
| --- | --- | --- |
| [backend/pyproject.toml](../backend/pyproject.toml) | Python project metadata, runtime deps, dev deps, pytest config, Ruff excludes. | Use `uv sync --extra dev`; validate with Ruff, mypy, pytest. |
| [backend/.env.example](../backend/.env.example) | Environment template. | Copy to `.env`; never commit real secrets. |
| [backend/alembic.ini](../backend/alembic.ini) | Alembic config. | Migration commands run from `backend`. |
| [backend/app/main.py](../backend/app/main.py) | FastAPI bootstrap: lifespan seeding, CORS, exception handlers, `/health`, API router include. | Change only for app-wide behavior. |
| [backend/app/config/settings.py](../backend/app/config/settings.py) | Pydantic settings from `.env`; resolves DB URL, JWT, CORS, seed admin, approved catalog path. | Add env vars here first. |
| [backend/app/entrypoints/api/router.py](../backend/app/entrypoints/api/router.py) | API router composition and `/api/health`. | Add route modules here. |
| [backend/app/entrypoints/api/dependencies.py](../backend/app/entrypoints/api/dependencies.py) | FastAPI DI factory functions, singleton services, bearer auth, role guards. | Wire repositories/services or auth rules here. |

### Backend Layers

| Layer | Paths | Responsibility |
| --- | --- | --- |
| Entrypoints | [backend/app/entrypoints/api/routes](../backend/app/entrypoints/api/routes) | Thin FastAPI handlers grouped by API surface: auth, profile, catalog, booking, recommendation, admin, store. |
| Use cases | [backend/app/use_cases](../backend/app/use_cases) | Business actions; one class per action or closely related action. |
| Domain | [backend/app/domain](../backend/app/domain) | Pure entities, enums, and policies. No FastAPI or SQLAlchemy dependencies. |
| Ports | [backend/app/ports](../backend/app/ports) | Repository/service protocols consumed by use cases. |
| Adapters | [backend/app/adapters](../backend/app/adapters) | SQLAlchemy repositories/models, JWT, password hashing, clock, and AI adapters. |
| DTOs | [backend/app/dto](../backend/app/dto) | Pydantic API request/response models and mapping helpers. |
| Shared | [backend/app/shared](../backend/app/shared) | App errors, HTTP error payloads, pagination, constants, serialization helpers. |

### Backend Route Files

| Path | Purpose |
| --- | --- |
| [backend/app/entrypoints/api/routes/auth_routes.py](../backend/app/entrypoints/api/routes/auth_routes.py) | Register, login, password reset, and `/auth/me`. |
| [backend/app/entrypoints/api/routes/profile_routes.py](../backend/app/entrypoints/api/routes/profile_routes.py) | Current customer profile read/write. |
| [backend/app/entrypoints/api/routes/catalog_routes.py](../backend/app/entrypoints/api/routes/catalog_routes.py) | Public string catalog list/detail. |
| [backend/app/entrypoints/api/routes/booking_routes.py](../backend/app/entrypoints/api/routes/booking_routes.py) | Customer booking create/list/detail. |
| [backend/app/entrypoints/api/routes/recommendation_routes.py](../backend/app/entrypoints/api/routes/recommendation_routes.py) | Recommendation preview/profile endpoints. |
| [backend/app/entrypoints/api/routes/admin_routes.py](../backend/app/entrypoints/api/routes/admin_routes.py) | Admin strings, inventory, bookings, status updates, check-in, queue, settings, analytics, logs. |
| [backend/app/entrypoints/api/routes/store_routes.py](../backend/app/entrypoints/api/routes/store_routes.py) | Public slot listing. |

### Backend Domains And Use Cases

| Domain | Key Files | Notes |
| --- | --- | --- |
| Auth | `domain/auth`, `use_cases/auth`, `dto/auth.py`, user/password-reset repositories | Phone-first registration/login, JWT token payloads, password reset codes. |
| Profile | `domain/profile`, `use_cases/profile`, `dto/profile.py` | Customer recommendation preference profile. |
| Catalog | `domain/catalog`, `use_cases/catalog`, `dto/catalog.py` | String catalog plus admin inventory fields and approved-catalog guard. |
| Booking | `domain/booking`, `use_cases/booking`, `dto/booking.py` | Booking creation, list/detail, admin status transitions, status note validation. |
| Store | `domain/store`, `use_cases/store`, `dto/store.py` | Business hours, slots, check-in, service queue, store settings, analytics. |
| Recommendation | `domain/recommendation`, `use_cases/recommendation`, `dto/recommendation.py` | Recommendation generation and admin log listing. |

When adding behavior, follow the clean-architecture direction:
`routes -> use_cases -> domain/ports -> adapters`.

### Backend Persistence And Migrations

| Path | Purpose |
| --- | --- |
| [backend/app/adapters/persistence/sqlalchemy/session.py](../backend/app/adapters/persistence/sqlalchemy/session.py) | SQLAlchemy engine/session lifecycle, schema helpers, DB health checks. |
| [backend/app/adapters/persistence/sqlalchemy/base.py](../backend/app/adapters/persistence/sqlalchemy/base.py) | Declarative base. |
| [backend/app/adapters/persistence/sqlalchemy/models](../backend/app/adapters/persistence/sqlalchemy/models) | ORM models for users, profiles, strings, bookings, business hours, settings, recommendation logs, password reset codes. |
| [backend/app/adapters/persistence/sqlalchemy/repositories](../backend/app/adapters/persistence/sqlalchemy/repositories) | Concrete repository implementations and ORM-domain mappers. |
| [backend/app/adapters/persistence/sqlalchemy/catalog_seed.py](../backend/app/adapters/persistence/sqlalchemy/catalog_seed.py) | Approved catalog parsing and seed/default derivation. |
| [backend/app/adapters/persistence/sqlalchemy/seed.py](../backend/app/adapters/persistence/sqlalchemy/seed.py) | Runtime seed users, catalog seed, and store defaults. |
| [backend/migrations/env.py](../backend/migrations/env.py) | Alembic migration environment. |
| [backend/migrations/versions](../backend/migrations/versions) | Schema history from unified backend through store ops tables. |
| [backend/data/raw/badminton_strings_recommender.jsonl](../backend/data/raw/badminton_strings_recommender.jsonl) | Fallback approved string catalog source. |

### Backend AI Compatibility Package

| Path | Purpose |
| --- | --- |
| [backend/ai_service/app.py](../backend/ai_service/app.py) | Standalone compatibility FastAPI app with internal API key guard. |
| [backend/ai_service/main.py](../backend/ai_service/main.py) | Standalone service entrypoint. |
| [backend/ai_service/service.py](../backend/ai_service/service.py) | `RecommendationService` compatibility facade for recommend, explain, review analysis, and RAG-like lookup. |
| [backend/ai_service/data_loader.py](../backend/ai_service/data_loader.py) | Loads CSV or JSONL string matrix/review signals and normalizes scores. |
| [backend/ai_service/schemas.py](../backend/ai_service/schemas.py) | Legacy combined Pydantic schemas. |
| [backend/ai_service/schemas](../backend/ai_service/schemas) | Split schemas for recommendation, review analysis, and RAG. |
| [backend/ai_service/services/recommendation_engine.py](../backend/ai_service/services/recommendation_engine.py) | Pure recommendation scoring helpers used by compatibility service. |
| [backend/ai_service/services/review_analysis.py](../backend/ai_service/services/review_analysis.py) | Rule-based review aspect aggregation. |
| [backend/ai_service/services/rag.py](../backend/ai_service/services/rag.py) | Lightweight RAG-style matching helper. |
| [backend/ai_service/core/config.py](../backend/ai_service/core/config.py) | AI service-specific settings. |

Active public API calls use AI through `backend/app/adapters/services/ai/*`, not
through a separate internal HTTP service by default.

### Backend Tests

| Path | Purpose |
| --- | --- |
| [backend/tests/conftest.py](../backend/tests/conftest.py) | Test env defaults and per-test SQLite DB reset/seed fixture. |
| [backend/tests/test_unified_backend_flows.py](../backend/tests/test_unified_backend_flows.py) | End-to-end API flow coverage: auth, profile, booking, admin controls, recommendation logs, store ops. |
| [backend/tests/test_sqlalchemy_repositories.py](../backend/tests/test_sqlalchemy_repositories.py) | Repository persistence behavior. |
| [backend/tests/test_recommendation_use_case.py](../backend/tests/test_recommendation_use_case.py) | Recommendation use-case behavior. |
| [backend/tests/test_booking_policies.py](../backend/tests/test_booking_policies.py) | Booking domain status transition and note policies. |
| [backend/tests/test_ai_service_api.py](../backend/tests/test_ai_service_api.py) | AI compatibility API coverage. |
| [backend/tests/test_ai_service_service.py](../backend/tests/test_ai_service_service.py) | AI service/facade coverage. |

## NLP Workbench

NLP lives in [ml/nlp-workbench](../ml/nlp-workbench). It is an offline notebook
workflow, not a public runtime service.

| Path | Purpose |
| --- | --- |
| [ml/nlp-workbench/README.md](../ml/nlp-workbench/README.md) | Notebook inputs, outputs, and run instructions. |
| [ml/nlp-workbench/requirements.txt](../ml/nlp-workbench/requirements.txt) | Notebook Python dependencies. |
| [ml/nlp-workbench/stringsense_complete_absa_pipeline_notebook.ipynb](../ml/nlp-workbench/stringsense_complete_absa_pipeline_notebook.ipynb) | Main pipeline; run top-to-bottom to generate backend recommendation artifacts. |
| [ml/nlp-workbench/stringsense_absa_labeling_notebook.ipynb](../ml/nlp-workbench/stringsense_absa_labeling_notebook.ipynb) | Labeling/support notebook for ABSA data work. |
| [ml/nlp-workbench/data/domain_dictionary_optimized_v6.csv](../ml/nlp-workbench/data/domain_dictionary_optimized_v6.csv) | Domain dictionary input. |
| [ml/nlp-workbench/data/normalization_rules_v6.csv](../ml/nlp-workbench/data/normalization_rules_v6.csv) | Text/string normalization rules. |
| [ml/nlp-workbench/data/nlp_absa_long_dataset_latest.csv](../ml/nlp-workbench/data/nlp_absa_long_dataset_latest.csv) | Long-form ABSA dataset input. |
| [ml/nlp-workbench/data/nlp_absa_high_confidence_latest.csv](../ml/nlp-workbench/data/nlp_absa_high_confidence_latest.csv) | High-confidence ABSA dataset input. |
| [ml/nlp-workbench/outputs/.gitkeep](../ml/nlp-workbench/outputs/.gitkeep) | Keeps the generated-output directory in git. |

The backend expects generated files such as:

- `ml/nlp-workbench/outputs/patched_practical_string_feature_matrix.csv`
- `ml/nlp-workbench/outputs/rule_based_review_aspect_signals.csv`

Generated notebook outputs should stay out of commits unless the task explicitly
asks to version a specific artifact.

## Common Change Recipes

| Task | Start Here | Then Check |
| --- | --- | --- |
| Add a mobile screen | `mobile/app/<role>/...` | Shared components in `mobile/components`, route guards, `types/domain.ts`. |
| Change mobile visual primitives | `mobile/components/ui/*` | `mobile/components/shared/*`, screenshots in `mobile/output`. |
| Add a backend endpoint | `backend/app/entrypoints/api/routes/*` | Matching use case, DTO, port/repository, tests, `backend/docs/api-contract.md`. |
| Change business rules | `backend/app/domain/*/policies.py` or `backend/app/use_cases/*` | Route DTOs, tests for policy/use case. |
| Change database schema | `backend/app/adapters/persistence/sqlalchemy/models/*` | Alembic revision, repositories, `backend/docs/database.md`, tests. |
| Change recommendation behavior | `backend/app/adapters/services/ai/recommendation_engine_adapter.py` and `backend/ai_service/*` | NLP outputs and recommendation tests. |
| Change mobile/backend field names | `backend/app/dto/*`, `mobile/types/backend.ts`, `mobile/services/backendMappers.ts` | API contract docs and backend/mobile validation. |
| Regenerate NLP artifacts | `ml/nlp-workbench/*.ipynb` | Backend `.env` `AI_*_PATH` values and generated output files. |

## Validation Shortlist

Prefer the commands in [AGENTS.md](../AGENTS.md). Minimum checks by scope:

- Docs-only change: inspect Markdown diff; no build normally required.
- Mobile code change: `cd mobile && npx tsc --noEmit`.
- Backend code change: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/pytest -v`.
- Backend contract/schema change: add or update tests, update `backend/docs/api-contract.md` and/or `backend/docs/database.md`.
- Cross-workspace change: run the relevant backend and mobile checks, then smoke the mobile app against `EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api`.
