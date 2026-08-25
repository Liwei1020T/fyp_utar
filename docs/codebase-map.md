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
6. Read [ml/nlp-workbench-latest/README.md](../ml/nlp-workbench-latest/README.md) before regenerating AI/NLP artifacts.

## Workspace Roots

| Path | Purpose | Open When |
| --- | --- | --- |
| [AGENTS.md](../AGENTS.md) | Repo-specific rules, validation commands, architecture boundaries, and done criteria. | Starting any task in this repo. |
| [README.md](../README.md) | Human quick start for the integrated mobile, backend, and NLP workspace. | Onboarding, demo setup, backend/mobile connection setup. |
| [compose.yaml](../compose.yaml) | Local Postgres 16 service on host port `55432`. | Backend needs local database state. |
| [docs/README.md](./README.md) | Workspace documentation index. | Finding existing docs. |
| [docs/fyp1-scope.md](./fyp1-scope.md) | FYP1 included/deferred scope, recommendation positioning, and demo proof. | Changing visible demo scope or deciding whether a feature is FYP1 or FYP2. |
| [docs/plans/mock-page-remediation.md](./plans/mock-page-remediation.md) | Current mock-data page inventory and external integration boundaries. | Checking whether a route still depends on mock or local business data. |
| [docs/production-hardening-acceptance-2026-08-24.md](./production-hardening-acceptance-2026-08-24.md) | Production Docker/security hardening, fresh-database runtime proof, and current player/admin acceptance gates. | Preparing or reviewing the controlled Cloudflare Tunnel deployment. |
| [docs/customer-admin-acceptance-2026-07-24.md](./customer-admin-acceptance-2026-07-24.md) | Current customer and administrator browser acceptance, cross-role persistence proof, and quality gates. | Reviewing which live reads and writes were exercised against PostgreSQL. |
| [docs/qr-payment-acceptance-2026-08-18.md](./qr-payment-acceptance-2026-08-18.md) | QR-transfer implementation evidence, security boundaries, and unverified device/browser checks. | Reviewing the manual payment-proof flow. |
| [docs/admin-acceptance-2026-07-23.md](./admin-acceptance-2026-07-23.md) | Historical administrator-only browser acceptance and restoration record. | Reviewing the earlier admin-specific acceptance run. |
| [docs/codebase-map.md](./codebase-map.md) | This low-token source map. | Deciding which source files are worth opening. |

Local archive files such as `backend.zip`, `ml.zip`, `stringsence.zip`, and
notebook export folders are snapshots or generated handoff artifacts. Do not
treat them as active source unless a task explicitly asks to restore or compare
against them.

## Mobile App

Mobile lives in [mobile](../mobile). It is an Expo Router React Native app using
TypeScript, HeroUI Native, Uniwind, Zustand, React Hook Form, and Zod. Zustand
owns the current live-session hydration boundary; there is no parallel React
Query cache owner.

### Mobile Config And Runtime

| Path | Purpose | Notes |
| --- | --- | --- |
| [mobile/package.json](../mobile/package.json) | Expo scripts and dependency versions. | Main scripts are `npm run web`, `npm run ios`, `npm run android`; typecheck uses `npx tsc --noEmit`. |
| [mobile/.nvmrc](../mobile/.nvmrc) | Node version pin. | Pins `24.18.0`; run `nvm use` before installing or running the app. |
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
| [mobile/app/_layout.tsx](../mobile/app/_layout.tsx) | Composition root: imports `global.css`, restores and validates native SecureStore or current-tab Web sessions, wraps `GestureHandlerRootView` and `HeroUINativeProvider`, and renders the root stack. |
| [mobile/app/index.tsx](../mobile/app/index.tsx) | Initial redirect based on current user role/session. |
| [mobile/app/auth/_layout.tsx](../mobile/app/auth/_layout.tsx) | Auth stack layout and redirect guard for already-authenticated users. |
| [mobile/app/auth/welcome.tsx](../mobile/app/auth/welcome.tsx) | Role-aware welcome/entry screen. |
| [mobile/app/auth/login.tsx](../mobile/app/auth/login.tsx) | Login form; registered players and operator-configured admins use the backend auth flow. |
| [mobile/app/auth/register.tsx](../mobile/app/auth/register.tsx) | Player registration form against backend session bridge. |
| [mobile/app/auth/forgot-password.tsx](../mobile/app/auth/forgot-password.tsx) | Password reset code request/reset flow. |
| [mobile/app/player/_layout.tsx](../mobile/app/player/_layout.tsx) | Player route-group guard. |
| [mobile/app/player/(tabs)/_layout.tsx](../mobile/app/player/%28tabs%29/_layout.tsx) | Player tab shell. |
| [mobile/app/player/(tabs)/home.tsx](../mobile/app/player/%28tabs%29/home.tsx) | Player dashboard and quick actions. |
| [mobile/app/player/(tabs)/strings.tsx](../mobile/app/player/%28tabs%29/strings.tsx) | String catalog browsing and sorting. |
| [mobile/app/player/(tabs)/recommend.tsx](../mobile/app/player/%28tabs%29/recommend.tsx) | Recommendation input form and backend recommendation trigger. |
| [mobile/app/player/(tabs)/bookings.tsx](../mobile/app/player/%28tabs%29/bookings.tsx) | Player booking list and filtering. |
| [mobile/app/player/(tabs)/chat.tsx](../mobile/app/player/%28tabs%29/chat.tsx) | Live player human-support list for booking-linked and booking-free threads. |
| [mobile/app/player/(tabs)/profile.tsx](../mobile/app/player/%28tabs%29/profile.tsx) | Player profile overview. |
| [mobile/app/player/bookings/new.tsx](../mobile/app/player/bookings/new.tsx) | Booking creation form and slot/string selection. |
| [mobile/app/player/bookings/summary.tsx](../mobile/app/player/bookings/summary.tsx) | Booking draft confirmation summary. |
| [mobile/app/player/bookings/[id].tsx](../mobile/app/player/bookings/[id].tsx) | Player booking detail. |
| [mobile/app/player/bookings/[id]/tracking.tsx](../mobile/app/player/bookings/[id]/tracking.tsx) | Service timeline screen. |
| [mobile/app/player/payments/[bookingId].tsx](../mobile/app/player/payments/%5BbookingId%5D.tsx) | Persisted booking payment request and server-validated wallet checkout. |
| [mobile/app/player/payments/[bookingId]/result.tsx](../mobile/app/player/payments/%5BbookingId%5D/result.tsx) | Persisted payment status and reference result screen. |
| [mobile/app/player/strings/[id].tsx](../mobile/app/player/strings/[id].tsx) | String detail screen. |
| [mobile/app/player/strings/compare.tsx](../mobile/app/player/strings/compare.tsx) | String comparison flow. |
| [mobile/app/player/(tabs)/results.tsx](../mobile/app/player/%28tabs%29/results.tsx) | Recommendation result list. |
| [mobile/app/player/recommend/explain/[id].tsx](../mobile/app/player/recommend/explain/[id].tsx) | Exact-run dynamic Agent explanation with saved-rationale fallback. |
| [mobile/app/player/profile/edit.tsx](../mobile/app/player/profile/edit.tsx) | Editable recommendation/player profile form. |
| [mobile/app/player/chat/[id].tsx](../mobile/app/player/chat/%5Bid%5D.tsx) | Player human-support detail backed by persisted conversation state and messages. |
| [mobile/app/player/chatbot.tsx](../mobile/app/player/chatbot.tsx) | FYP-scoped guided-selection and string-comparison Agent with live store information and verified replacement-string actions. |
| [mobile/app/player/check-in.tsx](../mobile/app/player/check-in.tsx) | Expiring server-issued QR check-in token screen. |
| [mobile/app/player/feedback/[bookingId].tsx](../mobile/app/player/feedback/%5BbookingId%5D.tsx) | Creates or displays the structured feedback record for one completed owned booking. |
| [mobile/app/player/notifications.tsx](../mobile/app/player/notifications.tsx) | Owned backend event feed with persisted read IDs. |
| [mobile/app/player/notifications/preferences.tsx](../mobile/app/player/notifications/preferences.tsx) | Backend preferences shared by the in-app feed and OpenWA delivery. |
| [mobile/app/player/settings.tsx](../mobile/app/player/settings.tsx) | Account, password, privacy, deletion request, version, and logout controls. |
| [mobile/app/player/rackets.tsx](../mobile/app/player/rackets.tsx) | Owned physical Racket Passport list. |
| [mobile/app/player/rackets/new.tsx](../mobile/app/player/rackets/new.tsx) | Registers a new owned physical racket passport. |
| [mobile/app/player/rackets/[id].tsx](../mobile/app/player/rackets/%5Bid%5D.tsx) | Edits a physical racket passport and shows completed linked service history. |
| [mobile/app/player/wallet.tsx](../mobile/app/player/wallet.tsx) | Persisted wallet balance and verified transaction ledger. |
| [mobile/app/player/wallet/top-up.tsx](../mobile/app/player/wallet/top-up.tsx) | Creates a pending wallet top-up for admin verification. |
| [mobile/app/admin/_layout.tsx](../mobile/app/admin/_layout.tsx) | Admin route-group guard. |
| [mobile/app/admin/(tabs)/_layout.tsx](../mobile/app/admin/%28tabs%29/_layout.tsx) | Admin tab shell. |
| [mobile/app/admin/(tabs)/dashboard.tsx](../mobile/app/admin/%28tabs%29/dashboard.tsx) | Admin operational dashboard. |
| [mobile/app/admin/(tabs)/bookings.tsx](../mobile/app/admin/%28tabs%29/bookings.tsx) | Admin booking management list. |
| [mobile/app/admin/(tabs)/inventory.tsx](../mobile/app/admin/%28tabs%29/inventory.tsx) | Admin inventory list. |
| [mobile/app/admin/(tabs)/chat.tsx](../mobile/app/admin/%28tabs%29/chat.tsx) | Live booking/general human-support queue backed by persisted conversation state. |
| [mobile/app/admin/(tabs)/analytics.tsx](../mobile/app/admin/%28tabs%29/analytics.tsx) | Backend analytics summary and popular-string view. |
| [mobile/app/admin/bookings/[id].tsx](../mobile/app/admin/bookings/[id].tsx) | Admin booking detail and status updates. |
| [mobile/app/admin/inventory/[id].tsx](../mobile/app/admin/inventory/[id].tsx) | Admin inventory detail edits plus `show on home` shortcut for player-facing trending strings. |
| [mobile/app/admin/business-hours.tsx](../mobile/app/admin/business-hours.tsx) | Store business hours editor. |
| [mobile/app/admin/check-in.tsx](../mobile/app/admin/check-in.tsx) | Camera QR scan, secure token confirmation, and manual lookup fallback. |
| [mobile/app/admin/feedback.tsx](../mobile/app/admin/feedback.tsx) | Structured feedback filter, booking drill-down, and CSV export. |
| [mobile/app/admin/notifications.tsx](../mobile/app/admin/notifications.tsx) | In-app plus WhatsApp notification composition, delivery status, and resend. |
| [mobile/app/admin/recommendations/index.tsx](../mobile/app/admin/recommendations/index.tsx) | Admin recommendation run history list backed by the unified backend. |
| [mobile/app/admin/recommendations/[runId].tsx](../mobile/app/admin/recommendations/%5BrunId%5D.tsx) | Admin recommendation run detail with request/profile snapshots and score breakdown review. |
| [mobile/app/admin/service-queue.tsx](../mobile/app/admin/service-queue.tsx) | Live booking service queue lanes. |
| [mobile/app/admin/payments.tsx](../mobile/app/admin/payments.tsx) | Persisted payment monitor and verification actions. |
| [mobile/app/admin/settings.tsx](../mobile/app/admin/settings.tsx) | Store copy, notification category switches, trending strings, and admin password controls. |
| [mobile/app/admin/chat/[id].tsx](../mobile/app/admin/chat/%5Bid%5D.tsx) | Admin human-support reply screen with persisted read, resolve, and close actions. |

### Mobile State, Services, And Types

| Path | Purpose | Open When |
| --- | --- | --- |
| [mobile/store/appStore.ts](../mobile/store/appStore.ts) | Zustand source of truth for authenticated session state, API response snapshots, booking drafts, compare selection, single-store settings, and selector hooks. | UI state is stale, a successful API response needs caching, or session behavior changes. |
| [mobile/services/backendClient.ts](../mobile/services/backendClient.ts) | Shared fetch, timeout, error parsing, form/text response, and token-specific 401 behavior. | Changing transport behavior. |
| [mobile/services/backendApi.ts](../mobile/services/backendApi.ts) | Typed endpoint facade using `EXPO_PUBLIC_API_BASE_URL`. | Adding or changing live backend calls. |
| [mobile/services/backendMappers.ts](../mobile/services/backendMappers.ts) | Converts backend snake_case DTOs into mobile domain models and builds backend payloads from mobile state. | Backend contract changes or mobile/backend field names diverge. |
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
| [mobile/components/agent/AgentAnswerCard.tsx](../mobile/components/agent/AgentAnswerCard.tsx) | Shared grounded-answer renderer; source and suggested-question presentation remains preserved but inactive. |
| [mobile/components/chat/ChatBubble.tsx](../mobile/components/chat/ChatBubble.tsx) | Chat message bubble. |
| [mobile/components/payment/PaymentMethodCard.tsx](../mobile/components/payment/PaymentMethodCard.tsx) | Payment option card. |
| [mobile/components/rackets/RacketPassportCard.tsx](../mobile/components/rackets/RacketPassportCard.tsx) | Racket passport summary card. |
| [mobile/components/rackets/RacketModelSelector.tsx](../mobile/components/rackets/RacketModelSelector.tsx) | Authenticated standard-model selector with loading, retry, and custom-model fallback. |
| [mobile/components/analytics/MetricStatCard.tsx](../mobile/components/analytics/MetricStatCard.tsx) | Admin analytics metric card. |

### Mobile Visual Assets

| Path | Purpose |
| --- | --- |
| [mobile/assets](../mobile/assets) | Expo icon/splash/favicon assets. |
| [mobile/output](../mobile/output) | Tracked visual screenshots and Playwright snapshots for UI reference. The auth and admin snapshots were regenerated after API-only remediation on 2026-07-23; treat them as evidence artifacts, not runtime code. |
| [mobile/tests/heroui-compat.smoke.tsx](../mobile/tests/heroui-compat.smoke.tsx) | Smoke test for HeroUI compatibility wrappers. |

## Backend

Backend lives in [backend](../backend). The active runtime is FastAPI under
`backend/app`; its only active recommendation implementation is
`backend/app/domain/recommendation/scoring.py`.

### Backend Config And Runtime

| Path | Purpose | Notes |
| --- | --- | --- |
| [backend/pyproject.toml](../backend/pyproject.toml) | Python project metadata, runtime deps, dev deps, pytest config, Ruff excludes. | Use `uv sync --extra dev`; validate with Ruff, mypy, pytest. |
| [backend/.env.example](../backend/.env.example) | Environment template. | Copy to `.env`; never commit real secrets. |
| [backend/alembic.ini](../backend/alembic.ini) | Alembic config. | Migration commands run from `backend`. |
| [backend/app/main.py](../backend/app/main.py) | FastAPI bootstrap: lifespan seeding, CORS, exception handlers, `/health`, API router include. | Change only for app-wide behavior. |
| [backend/app/config/settings.py](../backend/app/config/settings.py) | Pydantic settings from `.env`; resolves DB URL, JWT, CORS, seed admin, approved catalog path. | Add env vars here first. |
| [backend/app/entrypoints/api/router.py](../backend/app/entrypoints/api/router.py) | API router composition and `/api/health`. | Add route modules here. |
| [backend/app/entrypoints/api/health.py](../backend/app/entrypoints/api/health.py) | Shared `/health` and `/api/health` database/artifact contract. | Keep both public health aliases behaviorally identical. |
| [backend/app/entrypoints/api/dependencies.py](../backend/app/entrypoints/api/dependencies.py) | FastAPI DI factory functions, singleton services, bearer auth, role guards. | Wire repositories/services or auth rules here. |

### Backend Layers

| Layer | Paths | Responsibility |
| --- | --- | --- |
| Entrypoints | [backend/app/entrypoints/api/routes](../backend/app/entrypoints/api/routes) | FastAPI handlers grouped by API surface. Reusable multi-step behavior delegates to use cases; request transaction ownership stays in `get_db`. |
| Use cases | [backend/app/use_cases](../backend/app/use_cases) | Business actions; one class per action or closely related action. |
| Domain | [backend/app/domain](../backend/app/domain) | Pure entities, enums, and policies. No FastAPI or SQLAlchemy dependencies. |
| Ports | [backend/app/ports](../backend/app/ports) | Repository/service protocols consumed by use cases. |
| Adapters | [backend/app/adapters](../backend/app/adapters) | SQLAlchemy repositories/models, JWT, password hashing, and clock. |
| DTOs | [backend/app/dto](../backend/app/dto) | Pydantic API request/response models and mapping helpers. |
| Shared | [backend/app/shared](../backend/app/shared) | App errors, HTTP error payloads, pagination, constants, serialization helpers. |

### Backend Route Files

| Path | Purpose |
| --- | --- |
| [backend/app/entrypoints/api/routes/auth_routes.py](../backend/app/entrypoints/api/routes/auth_routes.py) | Register, login, password reset/change, deletion request, and `/auth/me`. |
| [backend/app/entrypoints/api/routes/profile_routes.py](../backend/app/entrypoints/api/routes/profile_routes.py) | Current customer profile and privacy settings. |
| [backend/app/entrypoints/api/routes/catalog_routes.py](../backend/app/entrypoints/api/routes/catalog_routes.py) | Public string catalog list/detail. |
| [backend/app/entrypoints/api/routes/booking_routes.py](../backend/app/entrypoints/api/routes/booking_routes.py) | Customer booking create/list/detail, cancellation, and QR token issue. |
| [backend/app/entrypoints/api/routes/recommendation_routes.py](../backend/app/entrypoints/api/routes/recommendation_routes.py) | Recommendation preview/profile endpoints. |
| [backend/app/entrypoints/api/routes/agent_routes.py](../backend/app/entrypoints/api/routes/agent_routes.py) | Authenticated, rate-limited player Agent query endpoint and DeepSeek composition. |
| [backend/app/entrypoints/api/routes/admin_routes.py](../backend/app/entrypoints/api/routes/admin_routes.py) | Admin strings, inventory, bookings, secure check-in, queue, settings, and recommendation logs. |
| [backend/app/entrypoints/api/routes/admin_engagement_routes.py](../backend/app/entrypoints/api/routes/admin_engagement_routes.py) | Admin feedback export, device tokens, notification delivery, and resend. |
| [backend/app/entrypoints/api/routes/admin_analytics_routes.py](../backend/app/entrypoints/api/routes/admin_analytics_routes.py) | Admin analytics summary and popular-string reporting. |
| [backend/app/entrypoints/api/routes/store_routes.py](../backend/app/entrypoints/api/routes/store_routes.py) | Public slot listing. |
| [backend/app/entrypoints/api/routes/commerce_routes.py](../backend/app/entrypoints/api/routes/commerce_routes.py) | Booking quotes, QR/cash payments, payment proofs, wallet ledger/top-ups, and admin verification. |
| [backend/app/entrypoints/api/routes/notification_routes.py](../backend/app/entrypoints/api/routes/notification_routes.py) | Owned notification feed, read IDs, preferences, and device token registration. |
| [backend/app/entrypoints/api/routes/booking_conversation_routes.py](../backend/app/entrypoints/api/routes/booking_conversation_routes.py) | Player/admin booking-linked and booking-free human-support lifecycle and messages. |
| [backend/app/entrypoints/api/routes/racket_feedback_routes.py](../backend/app/entrypoints/api/routes/racket_feedback_routes.py) | Server-validated standard racket catalogue, owned physical rackets, and completed-booking feedback. |
| [backend/app/entrypoints/api/routes/media_routes.py](../backend/app/entrypoints/api/routes/media_routes.py) | Time-limited signed access to persisted upload media. |

### Backend Domains And Use Cases

| Domain | Key Files | Notes |
| --- | --- | --- |
| Auth | `domain/auth`, `use_cases/auth`, `dto/auth.py`, user/password-reset repositories | Phone-first registration/login, JWT token payloads, password reset codes. |
| Profile | `domain/profile`, `use_cases/profile`, `dto/profile.py` | Customer recommendation preference profile. |
| Catalog | `domain/catalog`, `use_cases/catalog`, `dto/catalog.py` | String catalog plus admin inventory fields and approved-catalog guard. |
| Booking | `domain/booking`, `use_cases/booking`, `dto/booking.py` | Booking creation, list/detail, admin status transitions, status note validation. |
| Store | `domain/store`, `use_cases/store`, `dto/store.py` | Business hours, slots, check-in, service queue, store settings, analytics. |
| Recommendation | `domain/recommendation`, `use_cases/recommendation`, `dto/recommendation.py` | Recommendation generation and admin log listing. |
| Agent | `use_cases/agent`, `adapters/services/agent`, `dto/agent.py` | FYP-scoped guided selection, string comparison, exact-run context, in-stock alternatives, live store information, read-only admin booking and inventory queries, DeepSeek transport, and validated response. |
| Commerce | `routes/commerce_routes.py`, `dto/commerce.py`, commerce models | Server quotes, payment verification, and append-only wallet ledger. |
| Notifications | `routes/notification_routes.py`, `dto/notifications.py`, notification models | Owned event feed, per-user read state, and persisted preferences. |
| Human support | `routes/booking_conversation_routes.py`, `dto/booking_conversation.py`, conversation models | Booking-linked support plus one reusable booking-free support thread per player. |
| Rackets and feedback | `routes/racket_feedback_routes.py`, `dto/racket_feedback.py`, racket/feedback models | Owned physical racket passports and one feedback record per completed booking. |

When adding reusable or multi-repository behavior, follow the dependency
direction `routes -> use_cases -> domain/ports`, with entrypoints composing
concrete adapters that implement those ports. Do not add a one-implementation
port for a compact CRUD flow unless it creates a real testing, provider, or
reuse seam.

### Backend Persistence And Migrations

| Path | Purpose |
| --- | --- |
| [backend/app/adapters/persistence/sqlalchemy/session.py](../backend/app/adapters/persistence/sqlalchemy/session.py) | SQLAlchemy engine/session lifecycle, request commit/rollback boundary, schema helpers, and DB health checks. |
| [backend/app/adapters/persistence/sqlalchemy/base.py](../backend/app/adapters/persistence/sqlalchemy/base.py) | Declarative base. |
| [backend/app/adapters/persistence/sqlalchemy/models](../backend/app/adapters/persistence/sqlalchemy/models) | ORM models for users, profiles, strings, bookings, conversations, notifications, rackets/feedback, commerce, business hours, settings, recommendation logs/runs, and password reset codes. |
| [backend/app/adapters/persistence/sqlalchemy/repositories](../backend/app/adapters/persistence/sqlalchemy/repositories) | Concrete repository implementations and ORM-domain mappers. |
| [backend/app/adapters/persistence/sqlalchemy/catalog_seed.py](../backend/app/adapters/persistence/sqlalchemy/catalog_seed.py) | Approved catalog parsing and seed/default derivation. |
| [backend/app/adapters/persistence/sqlalchemy/seed.py](../backend/app/adapters/persistence/sqlalchemy/seed.py) | Runtime seed users, catalog seed, and store defaults. |
| [backend/migrations/env.py](../backend/migrations/env.py) | Alembic migration environment. |
| [backend/migrations/versions](../backend/migrations/versions) | Schema history from the unified backend through the current single head `20260818_0032`. |
| [backend/scripts/alembic](../backend/scripts/alembic) | Canonical Alembic wrapper; removes macOS AppleDouble Python sidecars before delegating to Alembic. |
| [backend/data/raw/badminton_strings_recommender.jsonl](../backend/data/raw/badminton_strings_recommender.jsonl) | Fallback approved string catalog source. |


### Backend Tests

| Path | Purpose |
| --- | --- |
| [backend/tests/conftest.py](../backend/tests/conftest.py) | Test env defaults and per-test SQLite DB reset/seed fixture. |
| [backend/tests/test_unified_backend_flows.py](../backend/tests/test_unified_backend_flows.py) | End-to-end API flow coverage: auth, profile, booking, admin controls, recommendation logs, store ops. |
| [backend/tests/test_sqlalchemy_repositories.py](../backend/tests/test_sqlalchemy_repositories.py) | Repository persistence behavior. |
| [backend/tests/test_recommendation_use_case.py](../backend/tests/test_recommendation_use_case.py) | Recommendation use-case behavior. |
| [backend/tests/test_agent.py](../backend/tests/test_agent.py) | Agent tool bounds, ownership, provider payload, What-if mapping, auth, and API behavior. |
| [backend/tests/test_booking_policies.py](../backend/tests/test_booking_policies.py) | Booking domain status transition and note policies. |
| [backend/tests/test_booking_conversations.py](../backend/tests/test_booking_conversations.py) | Booking-support lifecycle, ownership, admin role, and closed-thread guards. |
| [backend/tests/test_commerce_quote.py](../backend/tests/test_commerce_quote.py) | Server-owned booking quote and ledger amount contract. |
| [backend/tests/test_notifications.py](../backend/tests/test_notifications.py) | Notification ownership, preference filtering, and persisted read IDs. |
| [backend/tests/test_rackets_feedback.py](../backend/tests/test_rackets_feedback.py) | Racket ownership/snapshots and completed-booking feedback rules. |
| [backend/tests/test_store_analytics.py](../backend/tests/test_store_analytics.py) | Persisted commerce analytics and store-local day boundary. |
| [backend/tests/test_transaction_atomicity.py](../backend/tests/test_transaction_atomicity.py) | Failure-injection coverage for recommendation, password-reset, and secure check-in transaction rollback. |
| [backend/tests/test_player_admin_operations.py](../backend/tests/test_player_admin_operations.py) | Secure QR, detailed feedback, device delivery, account security, and privacy flow. |

## NLP Workbench

NLP lives in [ml/nlp-workbench-latest](../ml/nlp-workbench-latest). It is the
canonical offline notebook workflow, not a public runtime service.

| Path | Purpose |
| --- | --- |
| [ml/nlp-workbench-latest/README.md](../ml/nlp-workbench-latest/README.md) | Canonical notebook inputs, outputs, and run instructions. |
| [ml/nlp-workbench-latest/requirements.in](../ml/nlp-workbench-latest/requirements.in) | Human-maintained direct dependencies for Python 3.13. |
| [ml/nlp-workbench-latest/requirements.txt](../ml/nlp-workbench-latest/requirements.txt) | Exact generated dependency lock with package hashes. |
| [ml/nlp-workbench-latest/scripts/run_experiment.py](../ml/nlp-workbench-latest/scripts/run_experiment.py) | Canonical ordered notebook runner, immutable run boundary, and two-run reproducibility check. |
| [ml/nlp-workbench-latest/src/stringsense_nlp](../ml/nlp-workbench-latest/src/stringsense_nlp) | Tested labeling, leakage, manifest, model, inference, and protected-asset logic. |
| [ml/nlp-workbench-latest/stringsense_complete_absa_pipeline_notebook_latest.ipynb](../ml/nlp-workbench-latest/stringsense_complete_absa_pipeline_notebook_latest.ipynb) | Thin complete-pipeline entry point; consumes labeling artifacts from the same run ID. |
| [ml/nlp-workbench-latest/stringsense_absa_labeling_notebook_latest.ipynb](../ml/nlp-workbench-latest/stringsense_absa_labeling_notebook_latest.ipynb) | Thin labeling entry point with deterministic review-text group split. |
| [ml/nlp-workbench-latest/data/domain_dictionary_optimized_v8.csv](../ml/nlp-workbench-latest/data/domain_dictionary_optimized_v8.csv) | Current domain dictionary input. |
| [ml/nlp-workbench-latest/data/normalization_rules_v8.csv](../ml/nlp-workbench-latest/data/normalization_rules_v8.csv) | Current text/string normalization rules. |
| [ml/nlp-workbench-latest/data/nlp_absa_long_dataset_latest.csv](../ml/nlp-workbench-latest/data/nlp_absa_long_dataset_latest.csv) | Historical pre-boundary output; preserved for audit, not used for training. |
| [ml/nlp-workbench-latest/data/nlp_absa_high_confidence_latest.csv](../ml/nlp-workbench-latest/data/nlp_absa_high_confidence_latest.csv) | Historical pre-boundary output; preserved for audit, not used for training. |
| [ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx](../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx) | Current 12-string MacBERT `nlp_review` source. |
| [ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx](../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx) | Preserved legacy V9 workbook; not merged with MacBERT. |

Experiments write only under ignored, create-once
`ml/nlp-workbench-latest/output/runs/<run-id>/` directories. The unified backend
public runtime default review source is:

- `ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`

No experiment run promotes itself. Replacing the canonical V9 workbook or any
standalone `AI_*_PATH` compatibility artifact requires a separate comparison and
explicit human approval.

## Common Change Recipes

| Task | Start Here | Then Check |
| --- | --- | --- |
| Add a mobile screen | `mobile/app/<role>/...` | Shared components in `mobile/components`, route guards, `types/domain.ts`. |
| Change mobile visual primitives | `mobile/components/ui/*` | `mobile/components/shared/*`, screenshots in `mobile/output`. |
| Add a backend endpoint | `backend/app/entrypoints/api/routes/*` | Matching use case, DTO, port/repository, tests, `backend/docs/api-contract.md`. |
| Change business rules | `backend/app/domain/*/policies.py` or `backend/app/use_cases/*` | Route DTOs, tests for policy/use case. |
| Change database schema | `backend/app/adapters/persistence/sqlalchemy/models/*` | Alembic revision, repositories, `backend/docs/database.md`, tests. |
| Change recommendation behavior | `backend/app/domain/recommendation/scoring.py` | Recommendation use-case tests, runtime-boundary test, NLP artifact contract, and Mobile rationale rendering. |
| Change mobile/backend field names | `backend/app/dto/*`, `mobile/types/backend.ts`, `mobile/services/backendMappers.ts` | API contract docs and backend/mobile validation. |
| Regenerate NLP artifacts | `ml/nlp-workbench-latest/scripts/run_experiment.py` | Run twice, inspect manifests/leakage/metrics, then request separate approval before changing backend or compatibility artifacts. |

## Validation Shortlist

Prefer the commands in [AGENTS.md](../AGENTS.md). Minimum checks by scope:

- Docs-only change: inspect Markdown diff; no build normally required.
- Mobile code change: `cd mobile && nvm use && npx tsc --noEmit`.
- Backend code change: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app tests && ./.venv/bin/pytest -v`.
- Backend contract/schema change: add or update tests, update `backend/docs/api-contract.md` and/or `backend/docs/database.md`.
- Cross-workspace change: run the relevant backend and mobile checks, then smoke the mobile app against `EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api`.
